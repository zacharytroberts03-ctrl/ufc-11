import type { AnalysisResult } from "@/lib/types";

// Ordered the way they read on the chart: offense top-half, defense bottom-half.
// Starting at top (12 o'clock) and going clockwise.
const AXES = [
  { agent: "ufc-striking-offense",   short: "STR", full: "Striking Off" },
  { agent: "ufc-wrestling-offense",  short: "WRS", full: "Wrestling Off" },
  { agent: "ufc-takedown-offense",   short: "TKD", full: "Takedown Off" },
  { agent: "ufc-grappling-offense",  short: "GRP", full: "Grappling Off" },
  { agent: "ufc-submission-offense", short: "SUB", full: "Submission Off" },
  { agent: "ufc-submission-defense", short: "SUB", full: "Submission Def" },
  { agent: "ufc-grappling-defense",  short: "GRP", full: "Grappling Def" },
  { agent: "ufc-takedown-defense",   short: "TKD", full: "Takedown Def" },
  { agent: "ufc-wrestling-defense",  short: "WRS", full: "Wrestling Def" },
  { agent: "ufc-striking-defense",   short: "STR", full: "Striking Def" },
] as const;

type Reports = AnalysisResult["specialist_reports"];

function extractRatings(reports: Reports | undefined, fighterName: string): (number | null)[] {
  if (!reports) return AXES.map(() => null);
  const fighterReports = reports[fighterName];
  if (!fighterReports) return AXES.map(() => null);
  return AXES.map(({ agent }) => {
    const parsed = fighterReports[agent];
    const r = parsed?.report?.rating_1_to_10;
    return typeof r === "number" && r >= 1 && r <= 10 ? r : null;
  });
}

interface Props {
  reports?: Reports;
  fighterName: string;
  color: string;       // hex stroke + fill (with alpha applied internally)
  size?: number;       // px
  showLabels?: boolean;
}

export default function FighterDecagon({
  reports,
  fighterName,
  color,
  size = 200,
  showLabels = true,
}: Props) {
  const ratings = extractRatings(reports, fighterName);
  const cx = size / 2;
  const cy = size / 2;
  const maxRadius = size * 0.36; // leaves room for labels
  const labelRadius = size * 0.46;

  // Each axis position around the circle. Start at -90deg (top) so the first
  // axis points up; go clockwise.
  const axisAngles = AXES.map((_, i) => -Math.PI / 2 + (i * 2 * Math.PI) / AXES.length);

  // Polygon points for the actual ratings.
  const ratingPoints = ratings.map((r, i) => {
    const value = r ?? 0; // missing ratings collapse to center
    const radius = (value / 10) * maxRadius;
    return {
      x: cx + radius * Math.cos(axisAngles[i]),
      y: cy + radius * Math.sin(axisAngles[i]),
      hasData: r !== null,
    };
  });

  const polygonPath = ratingPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Gridline polygons (at rating 2, 4, 6, 8, 10)
  const gridLevels = [2, 4, 6, 8, 10];
  const gridPolygons = gridLevels.map((level) => {
    const radius = (level / 10) * maxRadius;
    const pts = axisAngles.map((angle) => {
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);
      return `${x},${y}`;
    });
    return pts.join(" ");
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="select-none"
    >
      {/* Background gridlines */}
      {gridPolygons.map((points, i) => (
        <polygon
          key={i}
          points={points}
          fill="none"
          stroke="#3a3a3a"
          strokeWidth={i === gridLevels.length - 1 ? 1.5 : 0.5}
          opacity={i === gridLevels.length - 1 ? 0.7 : 0.35}
        />
      ))}

      {/* Axis spokes */}
      {axisAngles.map((angle, i) => (
        <line
          key={i}
          x1={cx}
          y1={cy}
          x2={cx + maxRadius * Math.cos(angle)}
          y2={cy + maxRadius * Math.sin(angle)}
          stroke="#2a2a2a"
          strokeWidth={0.5}
        />
      ))}

      {/* Filled rating polygon */}
      <polygon
        points={polygonPath}
        fill={color}
        fillOpacity={0.28}
        stroke={color}
        strokeWidth={1.75}
        strokeLinejoin="round"
      />

      {/* Vertices */}
      {ratingPoints.map((p, i) =>
        p.hasData ? (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={2.5}
            fill={color}
          />
        ) : null
      )}

      {/* Labels */}
      {showLabels &&
        AXES.map((axis, i) => {
          const angle = axisAngles[i];
          const x = cx + labelRadius * Math.cos(angle);
          const y = cy + labelRadius * Math.sin(angle);
          const rating = ratings[i];

          // Anchor based on quadrant
          let anchor: "start" | "middle" | "end" = "middle";
          const cosA = Math.cos(angle);
          if (cosA > 0.3) anchor = "start";
          else if (cosA < -0.3) anchor = "end";

          return (
            <g key={i}>
              <text
                x={x}
                y={y}
                textAnchor={anchor}
                fontSize={size < 180 ? 8 : 9}
                fontWeight={700}
                fill="#888"
                dominantBaseline="middle"
                style={{ letterSpacing: "0.05em" }}
              >
                {axis.short}
              </text>
              {rating !== null && (
                <text
                  x={x}
                  y={y + (size < 180 ? 9 : 11)}
                  textAnchor={anchor}
                  fontSize={size < 180 ? 8 : 9}
                  fontWeight={800}
                  fill={color}
                  dominantBaseline="middle"
                >
                  {rating}
                </text>
              )}
            </g>
          );
        })}
    </svg>
  );
}
