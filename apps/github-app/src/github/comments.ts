/**
 * Post acknowledgement comments in response to events. An invisible marker is
 * embedded so we can detect (and avoid) duplicate acks.
 */
import { createIssueComment, type GhRest, type Repo } from "@itpr/github-client";

/** Hidden HTML marker embedded in every ack comment. */
export const ACK_MARKER = "<!-- itpr:ack -->";

/** True if any existing comment body already carries the ack marker. */
export function alreadyAcked(existingBodies: string[]): boolean {
  return existingBodies.some((b) => b.includes(ACK_MARKER));
}

/** Post an ack comment (always). Returns the new comment url. */
export async function postAck(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  message: string,
): Promise<string> {
  const body = `${message}\n\n${ACK_MARKER}`;
  const { url } = await createIssueComment(gh, repo, issueNumber, body);
  return url;
}

/**
 * Post an ack only if one is not already present. Returns the url when posted,
 * or undefined when skipped as a duplicate.
 */
export async function postAckOnce(
  gh: GhRest,
  repo: Repo,
  issueNumber: number,
  message: string,
  existingBodies: string[],
): Promise<string | undefined> {
  if (alreadyAcked(existingBodies)) return undefined;
  return postAck(gh, repo, issueNumber, message);
}
