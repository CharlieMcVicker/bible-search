import React, { useState, useEffect } from "react";
import {
  Search,
  Loader2,
  Tag,
  ChevronLeft,
  ChevronRight,
  Play,
  Volume2,
} from "lucide-react";
import clsx from "clsx";
import TaggingDrawer from "./components/TaggingDrawer";

const SUBCLAUSE_LABELS = {
  advcl: "Adverbial Clause",
  relcl: "Relative Clause",
  ccomp: "Clausal Complement",
  xcomp: "Open Clausal Complement",
  acl: "Adjectival Clause",
  csubj: "Clausal Subject",
};

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [taggingMode, setTaggingMode] = useState(false);
  const [activeWord, setActiveWord] = useState(null);
  const [filters, setFilters] = useState({
    use_lemma: false,
    is_hypothetical: false,
    is_command: false,
    is_time_clause: false,
    subclause_types: [],
  });

  const performSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query && !filters.is_command && !filters.is_hypothetical) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        use_lemma: filters.use_lemma,
        is_hypothetical: filters.is_hypothetical ? "true" : "false",
        is_command: filters.is_command ? "true" : "false",
        is_time_clause: filters.is_time_clause ? "true" : "false",
      });

      filters.subclause_types.forEach((t) =>
        params.append("subclause_types", t),
      );

      const res = await fetch(`/api/search?${params}`);
      const data = await res.json();
      setResults(data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTagUpdated = (sentenceId, wordIndex, tag) => {
    setResults((prev) =>
      prev.map((r) => {
        if (r.ref_id === sentenceId) {
          const newTags = [...(r.tags || [])];
          const existingIdx = newTags.findIndex(
            (t) => t.word_index === wordIndex,
          );
          if (existingIdx >= 0) {
            newTags[existingIdx] = { word_index: wordIndex, tag };
          } else {
            newTags.push({ word_index: wordIndex, tag });
          }
          return { ...r, tags: newTags };
        }
        return r;
      }),
    );
  };

  const toggleFilter = (key) => {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="container py-8">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Cherokee Search</h1>
        <form onSubmit={performSearch} className="max-w-2xl mx-auto flex gap-2">
          <input
            className="input"
            placeholder="Search Cherokee sentences..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary flex items-center gap-2">
            {loading ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Search size={20} />
            )}
            Search
          </button>
        </form>

        <div className="flex flex-wrap justify-center gap-4 mt-6">
          {["use_lemma", "is_hypothetical", "is_command", "is_time_clause"].map(
            (f) => (
              <label
                key={f}
                className="flex items-center gap-2 cursor-pointer select-none"
              >
                <input
                  type="checkbox"
                  checked={filters[f]}
                  onChange={() => toggleFilter(f)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium capitalize">
                  {f.replace("is_", "").replace("_", " ")}
                </span>
              </label>
            ),
          )}
        </div>
      </header>

      <main>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">
            {results.length > 0
              ? `Results (${results.length})`
              : "Enter a search to begin"}
          </h2>
          <button
            onClick={() => setTaggingMode(!taggingMode)}
            className={clsx(
              "btn flex items-center gap-2",
              taggingMode ? "btn-primary" : "bg-slate-200",
            )}
          >
            <Tag size={18} />
            {taggingMode ? "Tagging Mode: ON" : "Enable Tagging"}
          </button>
        </div>

        <div className="grid gap-6">
          {results.map((r) => (
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
                              setActiveWord({
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
                <span className="text-xs font-mono text-slate-400">
                  {r.ref_id}
                </span>
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
          ))}
        </div>
      </main>

      <TaggingDrawer
        isOpen={!!activeWord}
        onClose={() => setActiveWord(null)}
        word={activeWord?.word}
        sentenceId={activeWord?.sentenceId}
        wordIndex={activeWord?.wordIndex}
        currentTag={
          activeWord
            ? results
                .find((r) => r.ref_id === activeWord.sentenceId)
                ?.tags?.find((t) => t.word_index === activeWord.wordIndex)?.tag
            : null
        }
        onTagSelected={(tag) =>
          handleTagUpdated(activeWord.sentenceId, activeWord.wordIndex, tag)
        }
      />
    </div>
  );
}
