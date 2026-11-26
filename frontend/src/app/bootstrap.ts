import { signInFromUrl } from "@/stores/authStore";

/**
 * Exchange a sign-in link's code (if any) before the first render, so the
 * app never fires its first requests without a token and never flashes
 * the sign-in screen on the way in.
 *
 * The app renders no matter what: `signInFromUrl` times out a stalled
 * request and records failures for the sign-in screen, and `finally`
 * covers anything unexpected, so the page is never left blank.
 */
export async function bootstrap(
  render: () => void,
  signIn: () => Promise<void> = signInFromUrl,
) {
  try {
    await signIn();
  } finally {
    render();
  }
}
