export function connectProjectEvents(projectId: string, url: string, onEvent: (event: any) => void, onStatus: (status: string) => void) {
  let closed = false;
  let socket: WebSocket | null = null;

  const open = () => {
    if (closed) return;
    socket = new WebSocket(url);
    socket.onopen = () => onStatus('CONNECTED');
    socket.onclose = () => {
      onStatus('DISCONNECTED');
      if (!closed) window.setTimeout(open, 2500);
    };
    socket.onerror = () => onStatus('ERROR');
    socket.onmessage = event => {
      try {
        onEvent(JSON.parse(event.data));
      } catch {
        onEvent({ event: 'RAW', data: event.data });
      }
    };
  };

  open();

  return () => {
    closed = true;
    socket?.close();
  };
}
