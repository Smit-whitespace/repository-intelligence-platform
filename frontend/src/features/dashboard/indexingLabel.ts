import type { FreshnessResult } from "@/types/api";
import { formatCount } from "@/lib/utils/format";

/** The Dashboard's "Indexing" value for a project's index state. */
export function indexingLabel(result: FreshnessResult): string {
  switch (result.state) {
    case "up_to_date":
    case "updated":
      return "Up to date";
    case "updating":
      return "Updating";
    case "failed":
      return "Update failed";
    case "not_indexed":
      return "Not indexed";
    case "incompatible":
      return "Needs reindex (different embedding model)";
    default: {
      const n =
        result.changed_files + result.added_files + result.removed_files;

      return `${formatCount(n, "file")} changed since indexing`;
    }
  }
}
