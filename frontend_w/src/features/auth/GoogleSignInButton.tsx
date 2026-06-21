"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";


type GoogleCredentialResponse = {
  credential?: string;
};

type GoogleAccountsId = {
  initialize: (config: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void;
  renderButton: (element: HTMLElement, options: { theme: string; size: string; width?: number }) => void;
};

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: GoogleAccountsId;
      };
    };
  }
}

export function GoogleSignInButton({ nextTo = "/dashboard" }: { nextTo?: string }) {
  const router = useRouter();
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !buttonRef.current) return;

    const handleCredential = async (response: GoogleCredentialResponse) => {
      if (!response.credential) {
        setError("Google did not return a credential.");
        return;
      }

      const result = await fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: response.credential }),
      });
      if (!result.ok) {
        const data = await result.json().catch(() => ({}));
        setError(data.google || data.detail || "Google sign in failed.");
        return;
      }

      router.push(nextTo);
      router.refresh();
    };

    const render = () => {
      if (!window.google?.accounts?.id || !buttonRef.current) return;
      buttonRef.current.innerHTML = "";
      window.google.accounts.id.initialize({ client_id: clientId, callback: handleCredential });
      window.google.accounts.id.renderButton(buttonRef.current, { theme: "outline", size: "large", width: 320 });
    };

    if (window.google?.accounts?.id) {
      render();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = render;
    script.onerror = () => setError("Unable to load Google sign in.");
    document.head.appendChild(script);
  }, [clientId, nextTo, router]);

  if (!clientId) {
    return (
      <Button className="w-full" type="button" variant="secondary" disabled>
        Google sign in not configured
      </Button>
    );
  }

  return (
    <div className="space-y-2">
      <div ref={buttonRef} />
      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}
    </div>
  );
}
