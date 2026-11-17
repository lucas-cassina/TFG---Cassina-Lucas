import { useState, useEffect, useRef, useCallback } from 'react';
import { telemetriaAPI } from '../api/client';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Conecta al SSE stream de telemetría.
 * Expone: sesionActiva, sesionInfo, alertasLive, cargando
 * onSesionCerrada(event) se llama con los datos del índice calculado.
 *
 * - Usa token SSE efímero (POST /telemetria/sse-token) para no exponer el JWT en la URL.
 * - Backoff exponencial con jitter en reconexiones.
 */
export function useSesionStream(onSesionCerrada) {
  const [sesionActiva, setSesionActiva] = useState(false);
  const [sesionInfo,   setSesionInfo]   = useState(null);
  const [alertasLive,  setAlertasLive]  = useState([]);
  const [cargando,     setCargando]     = useState(true);

  const esRef       = useRef(null);
  const retryRef    = useRef(null);
  const mountedRef  = useRef(true);
  const retryCount  = useRef(0);

  const onCerradaRef = useRef(onSesionCerrada);
  useEffect(() => { onCerradaRef.current = onSesionCerrada; }, [onSesionCerrada]);

  const conectar = useCallback(async () => {
    if (!mountedRef.current) return;
    const token = localStorage.getItem('cias_token');
    if (!token) return;

    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    // Solicitar token SSE efímero (60 s, single-use) via axios para que el
    // interceptor de 401 dispare cias:unauthorized si el JWT fue revocado.
    let sseToken;
    try {
      const resp = await telemetriaAPI.obtenerSseToken();
      if (!mountedRef.current) return;
      sseToken = resp.data.sse_token;
    } catch {
      return;
    }

    const url = `${API_BASE}/telemetria/stream?sse_token=${encodeURIComponent(sseToken)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      if (!mountedRef.current) return;
      retryCount.current = 0;
      try {
        const event = JSON.parse(e.data);
        if (event.tipo === 'sesion_abierta') {
          setSesionActiva(true);
          setSesionInfo({ sesion_id: event.sesion_id, inicio: event.inicio });
          setAlertasLive([]);
        } else if (event.tipo === 'alerta') {
          setAlertasLive((prev) => [event, ...prev].slice(0, 20));
        } else if (event.tipo === 'sesion_cerrada') {
          setSesionActiva(false);
          setSesionInfo(null);
          setAlertasLive([]);
          onCerradaRef.current?.(event);
        }
      } catch { /* JSON parse error — ignorar */ }
    };

    es.onerror = () => {
      es.close();
      esRef.current = null;
      if (mountedRef.current) {
        // Backoff exponencial con jitter para evitar reconexiones simultáneas
        const base = Math.min(1000 * Math.pow(2, retryCount.current), 30_000);
        const jitter = Math.random() * 1000;
        retryCount.current += 1;
        retryRef.current = setTimeout(conectar, base + jitter);
      }
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    const token = localStorage.getItem('cias_token');
    if (!token) {
      setCargando(false);
      conectar();
      return;
    }

    const headers = { Authorization: `Bearer ${token}` };
    fetch(`${API_BASE}/telemetria/sesion/activa`, { headers })
      .then((r) => r.json())
      .then(async (data) => {
        if (!mountedRef.current) return;
        if (data.activa) {
          setSesionActiva(true);
          setSesionInfo({ sesion_id: data.sesion_id, inicio: data.inicio });
          try {
            const r = await fetch(`${API_BASE}/telemetria/alertas`, { headers });
            const alertas = await r.json();
            if (mountedRef.current && Array.isArray(alertas)) {
              const deEstaSesion = alertas
                .filter((a) => a.sesion_id === data.sesion_id)
                .map((a) => ({ tipo: 'alerta', ...a }));
              if (deEstaSesion.length > 0) setAlertasLive(deEstaSesion.slice(0, 20));
            }
          } catch { /* ignorar — las alertas llegarán por SSE */ }
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!mountedRef.current) return;
        setCargando(false);
        // Conectar DESPUÉS de que el estado histórico esté confirmado,
        // para evitar que los eventos SSE sean sobreescritos por el fetch.
        conectar();
      });

    return () => {
      mountedRef.current = false;
      clearTimeout(retryRef.current);
      esRef.current?.close();
      esRef.current = null;
    };
  }, [conectar]);

  return { sesionActiva, sesionInfo, alertasLive, cargando };
}
