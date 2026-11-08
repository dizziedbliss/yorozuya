import { Link } from "react-router";

/** Placeholder for pages that land in the next PR (stage 4c). */
export function Soon({ what, lost = false }: { what: string; lost?: boolean }) {
  return (
    <div className="wrap" style={{ paddingBlock: "40px" }}>
      <div className="notice">
        <h3>{lost ? "404. wrong turn." : `${what}: cooking.`}</h3>
        <p>{lost ? "nothing lives here. the jobs are back home." : "this page lands in the next PR. the Fresher page works today."}</p>
        <Link className="btn" to="/">Back to the jobs</Link>
      </div>
    </div>
  );
}
