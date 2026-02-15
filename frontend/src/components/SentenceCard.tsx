import React from "react";
import { Play } from "lucide-react";
import clsx from "clsx";
import { SearchResult, ActiveWord } from "../types";
import TaggingOptions from "./TaggingOptions";

interface SentenceCardProps {
  result: SearchResult;
  taggingMode: boolean;
  onWordClick: (activeWord: ActiveWord | null) => void;
  activeWordIndex?: number;
  onTagSelected: (tag: string | null) => void;
}

export default function SentenceCard({
  result: r,
  taggingMode,
  onWordClick,
  activeWordIndex,
  onTagSelected,
}: SentenceCardProps) {
  const syllabaryWords = r.syllabary.split(" ");
  const isActive = (index: number) => activeWordIndex === index;

  return (
    <div className="card">
      <div className="flex justify-between mb-4">
        <div className="flex flex-wrap gap-x-2 gap-y-4 text-2xl font-medium text-blue-700">
          {syllabaryWords.map((word, i) => {
            const tag = r.tags?.find((t) => t.word_index === i)?.tag;
            return (
              <div key={i} className="flex flex-col items-center">
                <span
                  className={clsx(
                    "rounded px-1 transition-colors relative",
                    taggingMode &&
                      "hover:bg-blue-100 cursor-pointer border border-dashed border-transparent hover:border-blue-400",
                    isActive(i) && "bg-blue-100 border-blue-400",
                  )}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (taggingMode) {
                      if (isActive(i)) {
                        onWordClick(null);
                      } else {
                        onWordClick({
                          word,
                          sentenceId: r.ref_id,
                          wordIndex: i,
                        });
                      }
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

      {activeWordIndex !== undefined && (
        <TaggingOptions
          word={syllabaryWords[activeWordIndex]}
          sentenceId={r.ref_id}
          wordIndex={activeWordIndex}
          currentTag={
            r.tags?.find((t) => t.word_index === activeWordIndex)?.tag
          }
          onTagSelected={onTagSelected}
        />
      )}

      {activeWordIndex === undefined && (
        <div className="grid md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate-50">
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
      )}
    </div>
  );
}
