import { useEffect, useState } from "react";

import { config } from "../config/env";
import { frameUrl } from "../lib/api";

export function useFrameImage(onError: (message: string) => void) {
  const [src, setSrc] = useState("");

  useEffect(() => {
    let alive = true;
    let timer: number | undefined;

    function requestFrame() {
      const next = new Image();
      next.onload = () => {
        if (!alive) {
          return;
        }
        setSrc(next.src);
        timer = window.setTimeout(requestFrame, config.frameRefreshMs);
      };
      next.onerror = () => {
        if (!alive) {
          return;
        }
        onError("Frame error");
        timer = window.setTimeout(requestFrame, config.frameRetryMs);
      };
      next.src = frameUrl();
    }

    requestFrame();
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [onError]);

  return src;
}
