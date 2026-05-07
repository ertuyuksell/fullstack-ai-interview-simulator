import { useEffect, useRef, useState } from 'react';

export function useAudioRecorder(stream) {
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [recording, setRecording] = useState(false);

  useEffect(() => () => stop().catch(() => {}), []); // eslint-disable-line

  function start() {
    if (!stream) return;
    chunksRef.current = [];
    const rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    rec.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
    rec.start();
    recorderRef.current = rec;
    setRecording(true);
  }

  function stop() {
    return new Promise((resolve) => {
      const rec = recorderRef.current;
      if (!rec || rec.state === 'inactive') return resolve(null);
      rec.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const buf = await blob.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
        setRecording(false);
        resolve(b64);
      };
      rec.stop();
    });
  }

  return { recording, start, stop };
}
