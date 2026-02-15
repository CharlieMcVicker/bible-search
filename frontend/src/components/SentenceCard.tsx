import React from "react";
import { Play } from "lucide-react";
import clsx from "clsx";
import { SearchResult, ActiveWord } from "../types";

interface SentenceCardProps {
  result: SearchResult;
  taggingMode: boolean;
  onWordClick: (activeWord: ActiveWord) => void;
}

export default function SentenceCard({
  result: r,
  taggingMode,
  onWordClick,
}: SentenceCardProps) {
  return (
    <div key={r.ref_id} className="card">
      <div className="flex justify-between mb-4">
        <div className="flex flex-wrap gap-x-2 gap-y-4 text-2xl font-medium text-blue-700">
          {r.syllabary.split(" ").map((word, i) => {
            const tag = r.tags?.find((t) => t.word_index === i)?.tag;
            return (
              <div key={i} className="flex flex-col items-center">
                <span
                  className={clsx(
                    "rounded px-1 transition-colors relative",
                    taggingMode &&
                      "hover:bg-blue-100 cursor-pointer border border-dashed border-transparent hover:border-blue-400",
                  )}
                  onClick={() => {
                    if (taggingMode) {
                      onWordClick({
                        word,
                        sentenceId: r.ref_id,
                        wordIndex: i,
                      });
                    }
                  }}
                >
                  {word}
                </span>
                {tag && (
                  <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-100 px-1 rounded-sm mt-1">
                    {tag}
                  </span>
                )}
              </div>
            );
          })}
        </div>
        <span className="text-xs font-mono text-slate-400">{r.ref_id}</span>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <div className="flex flex-wrap gap-x-2 font-bold text-slate-700 mb-1">
            {r.phonetic.split(" ").map((word, i) => (
              <React.Fragment key={i}>
                <span>{word}</span>{" "}
              </React.Fragment>
            ))}
          </div>
          <p className="text-slate-600">{r.english}</p>
        </div>
        <div className="flex items-center justify-end">
          {r.audio ? (
            <button className="btn bg-slate-100 hover:bg-slate-200 flex items-center gap-2">
              <Play size={16} fill="currentColor" /> Play Audio
            </button>
          ) : (
            <span className="text-sm text-slate-400 italic">
              No audio available
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
