import { signInFromUrl } from "@/stores/authStore";

/**
 * Exchange a sign-in link's code (if any) before the first render, so the
 * app never fires its first requests without a token and never flashes
 * the sign-in screen on the way in. `signInFromUrl` records any failure
 * for the sign-in screen and never throws, so the app always renders.
 */
export async function bootstrap(render: () => void) {
  await signInFromUrl();
  render();
}
