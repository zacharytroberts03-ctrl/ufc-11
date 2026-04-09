"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchCachedAnalysis, runAnalysis, fetchFighter } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";
import FighterVsHeader from "@/components/FighterVsHeader";
import AnalysisSection from "@/components/AnalysisSection";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function FightDetailPage() {
  const params = useParams<{ f1: string; f2: string }>();
  const router = useRouter();

  const f1 = decodeURIComponent(params.f1);
  const f2 = decodeURIComponent(params.f2);

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(true);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [f1ImgFallback, setF1ImgFallback] = useState<string | null>(null);
  const [f2ImgFallback, setF2ImgFallback] = useState<string | null>(null);

  useEffect(() => {
    fetchCachedAnalysis(f1, f2)
      .then(setAnalysis)
      .finally(() => setLoadingAnalysis(false));

    // Fetch photos independently so they show even without an analysis
    fetchFighter(f1).then((d) => { if (d?.photo_url) setF1ImgFallback(d.photo_url); });
    fetchFighter(f2).then((d) => { if (d?.photo_url) setF2ImgFallback(d.photo_url); });
  }, [f1, f2]);

  const handleRunAnalysis = async () => {
    setRunningAnalysis(true);
    setAnalysisError(null);
    try {
      const result = await runAnalysis(f1, f2, 100);
      setAnalysis(result);
    } catch (e) {
      setAnalysisError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setRunningAnalysis(false);
    }
  };

  const f1Img = analysis?.f1_img ?? f1ImgFallback;
  const f2Img = analysis?.f2_img ?? f2ImgFallback;
  const sections = analysis?.analysis_sections ?? {};

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Back button */}
      <button
        onClick={() => router.push("/")}
        className="flex items-center gap-2 text-ufc-muted hover:text-ufc-text text-sm font-semibold mb-6 transition-colors group"
      >
        <svg
          className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Fight Card
      </button>

      {/* Fighter VS Header */}
      <FighterVsHeader
        f1Name={f1}
        f2Name={f2}
        f1Img={f1Img}
        f2Img={f2Img}
        f1Debut={analysis?.f1_data?.ufc_debut}
        f2Debut={analysis?.f2_data?.ufc_debut}
      />

      {/* Analysis Section */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-black text-ufc-text uppercase tracking-wider">
            AI Fight Analysis
          </h2>
          {analysis && (
            <span className="text-xs text-ufc-muted">
              Generated {new Date(analysis.generated_at).toLocaleDateString()}
            </span>
          )}
        </div>

        {loadingAnalysis ? (
          <LoadingSpinner message="Checking for cached analysis..." />
        ) : analysis ? (
          <div className="space-y-1">
            {/* Side-by-side fighter profiles */}
            {(sections.f1_profile || sections.f2_profile) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {sections.f1_profile && (
                  <AnalysisSection
                    title={`${f1} — Style & Profile`}
                    content={sections.f1_profile}
                    icon="⚡"
                    defaultOpen={true}
                    accentColor="red"
                  />
                )}
                {sections.f2_profile && (
                  <AnalysisSection
                    title={`${f2} — Style & Profile`}
                    content={sections.f2_profile}
                    icon="⚡"
                    defaultOpen={true}
                    accentColor="red"
                  />
                )}
              </div>
            )}
            {sections.head2head && (
              <AnalysisSection
                title="Head-to-Head Breakdown"
                content={sections.head2head}
                icon="🥊"
                defaultOpen={true}
                accentColor="gold"
              />
            )}
            {sections.endings && (
              <AnalysisSection
                title="Most Likely Fight Endings"
                content={sections.endings}
                icon="🎯"
                defaultOpen={false}
                accentColor="gold"
              />
            )}
            {sections.betting && (
              <AnalysisSection
                title="Betting Recommendation"
                content={sections.betting}
                icon="💰"
                defaultOpen={false}
                accentColor="green"
              />
            )}
          </div>
        ) : (
          /* No analysis yet — show run button */
          <div className="card-elevated rounded-xl border-2 border-dashed border-ufc-red p-8 text-center">
            <div className="text-4xl mb-3">🥊</div>
            <h3 className="text-ufc-text font-bold text-lg mb-2">
              No analysis yet
            </h3>
            <p className="text-ufc-muted text-sm mb-6">
              Run the AI analysis to get fighter profiles, head-to-head breakdown,
              predicted endings, and betting recommendations.
            </p>

            {analysisError && (
              <div className="bg-ufc-red/10 border border-ufc-red/30 rounded-lg px-4 py-3 mb-4 text-ufc-red text-sm">
                {analysisError}
              </div>
            )}

            <button
              onClick={handleRunAnalysis}
              disabled={runningAnalysis}
              className="btn-red disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {runningAnalysis ? "Analyzing... (30-60s)" : "Run Full Analysis"}
            </button>

            {runningAnalysis && (
              <div className="mt-6">
                <LoadingSpinner message="Claude is analyzing this matchup..." />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
