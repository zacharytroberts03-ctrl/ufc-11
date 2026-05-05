import type { AnalysisResult } from "@/lib/types";

// Unique acronyms — O- prefix for offense, D- prefix for defense — so no two
// axes share a label. Order: 5 offense (top half clockwise from top), 5 defense
// (bottom half continuing clockwise back to top-left).
export const AXES = [
  { agent: "ufc-striking-offense",   short: "O-STR", full: "Striking Offense" },
  { agent: "ufc-wrestling-offense",  short: "O-WRS", full: "Wrestling Offense" },
  { agent: "ufc-takedown-offense",   short: "O-TKD", full: "Takedown Offense" },
  { agent: "ufc-grappling-offense",  short: "O-GRP", full: "Grappling Offense" },
  { agent: "ufc-submission-offense", short: "O-SUB", full: "Submission Offense" },
  { agent: "ufc-submission-defense", short: "D-SUB", full: "Submission Defense" },
  { agent: "ufc-grappling-defense",  short: "D-GRP", full: "Grappling Defense" },
  { agent: "ufc-takedown-defense",   short: "D-TKD", full: "Takedown Defense" },
  { agent: "ufc-wrestling-defense",  short: "D-WRS", full: "Wrestling Defense" },
  { agent: "ufc-striking-defense",   short: "D-STR", full: "Striking Defense" },
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
  color: string;
  size?: number;
  showLabels?: boolean;
}

// Padding around the chart so labels at the edges don't clip.
const PAD = 28;

export default function FighterDecagon({
  reports,
  fighterName,
  color,
  size = 200,
  showLabels = true,
}: Props) {
  const ratings = extractRatings(reports, fighterName);
  const viewSize = size + PAD * 2;
  const cx = viewSize / 2;
  const cy = viewSize / 2;
  const maxRadius = size * 0.42;
  const labelRadius = size * 0.52;

  // Each axis position around the circle. Start at -90deg (top) clockwise.
  const axisAngles = AXES.map((_, i) => -Math.PI / 2 + (i * 2 * Math.PI) / AXES.length);

  // Polygon points for the actual ratings.
  const ratingPoints = ratings.map((r, i) => {
    const value = r ?? 0;
    const radius = (value / 10) * maxRadius;
    return {
      x: cx + radius * Math.cos(axisAngles[i]),
      y: cy + radius * Math.sin(axisAngles[i]),
      hasData: r !== null,
    };
  });

  const polygonPath = ratingPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Gridline polygons at rating 2, 4, 6, 8, 10
  const gridLevels = [2, 4, 6, 8, 10];
  const gridPolygons = gridLevels.map((level) => {
    const radius = (level / 10) * maxRadius;
    return axisAngles
      .map((angle) => `${cx + radius * Math.cos(angle)},${cy + radius * Math.sin(angle)}`)
      .join(" ");
  });

  return (
    <svg
      width={viewSize}
      height={viewSize}
      viewBox={`0 0 ${viewSize} ${viewSize}`}
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
          <circle key={i} cx={p.x} cy={p.y} r={2.5} fill={color} />
        ) : null
      )}

      {/* Labels — single text per axis with the acronym + rating value */}
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
            <text
              key={i}
              x={x}
              y={y}
              textAnchor={anchor}
              fontSize={9}
              fontWeight={700}
              dominantBaseline="middle"
              style={{ letterSpacing: "0.04em" }}
            >
              <tspan fill="#999">{axis.short}</tspan>
              {rating !== null && (
                <tspan fill={color} fontWeight={800} dx="4">{rating}</tspan>
              )}
            </text>
          );
        })}
    </svg>
  );
}
