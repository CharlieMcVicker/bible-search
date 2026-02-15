import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import clsx from "clsx";
import SearchForm from "../components/SearchForm";
import { SearchResult, Filters } from "../types";
import { AVAILABLE_TAGS, TAG_LABELS } from "../constants";

const BATCH_SIZE = 50;

export default function TaggingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // Search state
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Batch of results fetched from server
  const [batch, setBatch] = useState<SearchResult[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);

  // Track skipped ref_ids so we don't show them again on re-fetch
  const skippedRefIds = useRef<Set<string>>(new Set());

  // Word cursor position within current sentence
  const [cursorIndex, setCursorIndex] = useState(0);

  // Tagging loading state
  const [tagLoading, setTagLoading] = useState(false);

  // Sync query from URL
  const query = searchParams.get("q") || "";
  const [localQuery, setLocalQuery] = useState(query);

  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  const filters: Filters = {
    use_lemma: searchParams.get("use_lemma") === "true",
    is_hypothetical: searchParams.get("is_hypothetical") === "true",
    is_command: searchParams.get("is_command") === "true",
    is_time_clause: searchParams.get("is_time_clause") === "true",
    untagged_only: true, // Always forced
    subclause_types: searchParams.getAll("subclause_types"),
    tag: searchParams.get("tag") || "",
  };

  const updateSearchParams = (newQuery: string, newFilters: Filters) => {
    const params = new URLSearchParams();
    if (newQuery) params.set("q", newQuery);
    if (newFilters.use_lemma) params.set("use_lemma", "true");
    if (newFilters.is_hypothetical) params.set("is_hypothetical", "true");
    if (newFilters.is_command) params.set("is_command", "true");
    if (newFilters.is_time_clause) params.set("is_time_clause", "true");
    if (newFilters.tag) params.set("tag", newFilters.tag);
    newFilters.subclause_types.forEach((t) =>
      params.append("subclause_types", t),
    );
    setSearchParams(params);
  };

  const fetchBatch = useCallback(
    async (offset = 0): Promise<{ results: SearchResult[]; total: number }> => {
      const params = new URLSearchParams({
        q: query,
        limit: String(BATCH_SIZE),
        offset: String(offset),
        use_lemma: String(filters.use_lemma),
        is_hypothetical: String(filters.is_hypothetical),
        is_command: String(filters.is_command),
        is_time_clause: String(filters.is_time_clause),
        untagged_only: "true",
      });
      if (filters.tag) params.append("tag", filters.tag);
      filters.subclause_types.forEach((t) =>
        params.append("subclause_types", t),
      );

      const res = await fetch(`/api/search?${params}`);
      const data = await res.json();
      return {
        results: (data.data || []) as SearchResult[],
        total: data.meta?.total || 0,
      };
    },
    [query, JSON.stringify(filters)],
  );

  const startTagging = useCallback(async () => {
    setLoading(true);
    setHasSearched(true);
    skippedRefIds.current = new Set();
    setCompletedCount(0);

    try {
      const { results, total } = await fetchBatch(0);
      // Filter out any skipped (should be empty at start)
      const filtered = results.filter(
        (r) => !skippedRefIds.current.has(r.ref_id),
      );
      setBatch(filtered);
      setTotalCount(total);
      setCurrentIndex(0);
      setCursorIndex(0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [fetchBatch]);

  // Trigger search on URL param changes.
  // Also auto-start on mount if URL has a query or filters.
  const filtersKey = JSON.stringify(filters);
  useEffect(() => {
    const hasParams =
      query ||
      filters.is_command ||
      filters.is_hypothetical ||
      filters.is_time_clause ||
      filters.tag ||
      filters.subclause_types.length > 0;

    if (hasParams) {
      startTagging();
    }
  }, [query, filtersKey]);

  const currentSentence: SearchResult | null =
    currentIndex < batch.length ? batch[currentIndex] : null;

  const syllabaryWords = currentSentence
    ? currentSentence.syllabary.split(" ")
    : [];

  // Get current tag for the word at cursor
  const getCurrentWordTag = (): string | undefined => {
    if (!currentSentence) return undefined;
    return currentSentence.tags?.find((t) => t.word_index === cursorIndex)?.tag;
  };

  const handleTagWord = async (tag: string) => {
    if (!currentSentence || tagLoading) return;

    setTagLoading(true);
    try {
      const response = await fetch(
        `/api/sentences/${currentSentence.ref_id}/tags`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ word_index: cursorIndex, tag }),
        },
      );
      if (response.ok) {
        // Update local state
        setBatch((prev) =>
          prev.map((r, i) => {
            if (i === currentIndex) {
              const newTags = [...(r.tags || [])];
              const existingIdx = newTags.findIndex(
                (t) => t.word_index === cursorIndex,
              );
              if (existingIdx >= 0) {
                newTags[existingIdx] = { word_index: cursorIndex, tag };
              } else {
                newTags.push({ word_index: cursorIndex, tag });
              }
              return { ...r, tags: newTags };
            }
            return r;
          }),
        );
      }
    } catch (err) {
      console.error("Failed to tag:", err);
    } finally {
      setTagLoading(false);
    }
  };

  const handleClearTag = async () => {
    if (!currentSentence || tagLoading) return;
    const existingTag = getCurrentWordTag();
    if (!existingTag) return;

    setTagLoading(true);
    try {
      const response = await fetch(
        `/api/sentences/${currentSentence.ref_id}/tags`,
        {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ word_index: cursorIndex }),
        },
      );
      if (response.ok) {
        setBatch((prev) =>
          prev.map((r, i) => {
            if (i === currentIndex) {
              const newTags = (r.tags || []).filter(
                (t) => t.word_index !== cursorIndex,
              );
              return { ...r, tags: newTags };
            }
            return r;
          }),
        );
      }
    } catch (err) {
      console.error("Failed to clear tag:", err);
    } finally {
      setTagLoading(false);
    }
  };

  const advanceToNext = async () => {
    if (!currentSentence) return;

    const wasTagged = (currentSentence.tags || []).length > 0;

    if (!wasTagged) {
      // Skipped — track so we don't re-show on re-fetch
      skippedRefIds.current.add(currentSentence.ref_id);
    }

    setCompletedCount((c) => c + 1);

    // Try to find next non-skipped in current batch
    let nextIdx = currentIndex + 1;
    while (
      nextIdx < batch.length &&
      skippedRefIds.current.has(batch[nextIdx].ref_id)
    ) {
      nextIdx++;
    }

    if (nextIdx < batch.length) {
      setCurrentIndex(nextIdx);
      setCursorIndex(0);
    } else {
      // Need to re-fetch — tagged items have dropped from server results,
      // so offset 0 gives fresh untagged results
      setLoading(true);
      try {
        const { results, total } = await fetchBatch(0);
        const filtered = results.filter(
          (r) => !skippedRefIds.current.has(r.ref_id),
        );
        setBatch(filtered);
        setTotalCount(total);
        setCurrentIndex(0);
        setCursorIndex(0);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
  };

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't capture keys when typing in inputs/selects
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "SELECT" ||
        target.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (!currentSentence) return;

      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          setCursorIndex((prev) => Math.max(0, prev - 1));
          break;
        case "ArrowRight":
          e.preventDefault();
          setCursorIndex((prev) =>
            Math.min(syllabaryWords.length - 1, prev + 1),
          );
          break;
        case "Enter":
          e.preventDefault();
          advanceToNext();
          break;
        case "Backspace":
          e.preventDefault();
          handleClearTag();
          break;
        default: {
          // Number keys 1-9 for tags
          const num = parseInt(e.key);
          if (num >= 1 && num <= AVAILABLE_TAGS.length) {
            e.preventDefault();
            handleTagWord(AVAILABLE_TAGS[num - 1]);
          }
          break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSentence, cursorIndex, syllabaryWords.length, tagLoading]);

  const currentWordTag = getCurrentWordTag();

  return (
    <div className="container py-8">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate("/")}
          className="btn bg-slate-100 flex items-center gap-2"
          title="Back to Home"
        >
          <ArrowLeft size={18} />
          Back
        </button>
        <h1 className="text-2xl font-bold" style={{ margin: 0 }}>
          Tagging Mode
        </h1>
      </div>

      <SearchForm
        query={localQuery}
        setQuery={setLocalQuery}
        filters={filters}
        setFilters={(f) =>
          updateSearchParams(localQuery, { ...f, untagged_only: true })
        }
        loading={loading}
        onSearch={() =>
          updateSearchParams(localQuery, { ...filters, untagged_only: true })
        }
      />

      {!hasSearched && (
        <div
          className="text-center mt-12"
          style={{ color: "var(--text-muted)" }}
        >
          <p className="text-lg">
            Enter a search query and press Search to begin tagging.
          </p>
          <p className="text-sm" style={{ marginTop: "0.5rem" }}>
            Only untagged sentences will be shown.
          </p>
        </div>
      )}

      {hasSearched && !loading && !currentSentence && (
        <div className="text-center mt-12">
          <div
            style={{
              fontSize: "3rem",
              marginBottom: "1rem",
            }}
          >
            🎉
          </div>
          <h2 className="text-xl font-semibold mb-4">All done!</h2>
          <p style={{ color: "var(--text-muted)" }}>
            No more untagged sentences match your search.
            {skippedRefIds.current.size > 0 && (
              <> ({skippedRefIds.current.size} skipped)</>
            )}
          </p>
        </div>
      )}

      {hasSearched && loading && (
        <div className="text-center mt-12">
          <div className="text-xl" style={{ color: "var(--text-muted)" }}>
            Loading sentences...
          </div>
        </div>
      )}

      {currentSentence && !loading && (
        <div style={{ marginTop: "2rem" }}>
          {/* Progress bar */}
          <div
            className="flex justify-between items-center mb-4"
            style={{ color: "var(--text-muted)" }}
          >
            <span className="text-sm font-medium">
              {completedCount + 1} of {totalCount} untagged
              {skippedRefIds.current.size > 0 && (
                <span style={{ marginLeft: "0.5rem", opacity: 0.7 }}>
                  ({skippedRefIds.current.size} skipped)
                </span>
              )}
            </span>
            <span className="text-xs font-mono">{currentSentence.ref_id}</span>
          </div>

          {/* Progress bar visual */}
          <div
            style={{
              height: "4px",
              background: "var(--border)",
              borderRadius: "2px",
              marginBottom: "1.5rem",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${
                  totalCount > 0 ? (completedCount / totalCount) * 100 : 0
                }%`,
                background: "var(--primary)",
                borderRadius: "2px",
                transition: "width 0.3s ease",
              }}
            />
          </div>

          {/* Sentence card */}
          <div className="card" style={{ padding: "2rem" }}>
            {/* Cherokee words with cursor */}
            <div
              className="flex flex-wrap gap-x-2"
              style={{
                gap: "0.5rem 0.75rem",
                marginBottom: "1.5rem",
              }}
            >
              {syllabaryWords.map((word, i) => {
                const tag = currentSentence.tags?.find(
                  (t) => t.word_index === i,
                )?.tag;
                const isCursor = i === cursorIndex;

                return (
                  <div
                    key={i}
                    className="flex"
                    style={{
                      flexDirection: "column",
                      alignItems: "center",
                    }}
                  >
                    <span
                      onClick={() => setCursorIndex(i)}
                      className={clsx("text-2xl font-medium")}
                      style={{
                        padding: "0.25rem 0.5rem",
                        borderRadius: "6px",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                        border: isCursor
                          ? "2px solid var(--primary)"
                          : "2px solid transparent",
                        background: isCursor ? "#eff6ff" : "transparent",
                        color: isCursor ? "var(--primary)" : "#1d4ed8",
                      }}
                    >
                      {word}
                    </span>
                    {tag && (
                      <span
                        className="text-xs uppercase font-bold"
                        style={{
                          color: "var(--primary)",
                          background: "#eff6ff",
                          padding: "0.125rem 0.5rem",
                          borderRadius: "4px",
                          marginTop: "0.25rem",
                          fontSize: "0.625rem",
                          letterSpacing: "0.05em",
                        }}
                      >
                        {tag}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Phonetic + English (always visible) */}
            <div
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "1rem",
                marginBottom: "1.5rem",
              }}
            >
              <div
                className="font-bold"
                style={{
                  color: "var(--text-main)",
                  marginBottom: "0.25rem",
                }}
              >
                {currentSentence.phonetic}
              </div>
              <p style={{ color: "var(--text-muted)", margin: 0 }}>
                {currentSentence.english}
              </p>
            </div>

            {/* Tag buttons */}
            <div
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "1rem",
              }}
            >
              <div
                className="text-xs font-bold uppercase"
                style={{
                  color: "var(--text-muted)",
                  letterSpacing: "0.1em",
                  marginBottom: "0.75rem",
                }}
              >
                Tag "{syllabaryWords[cursorIndex]}" as:
              </div>

              <div className="flex flex-wrap gap-2">
                {AVAILABLE_TAGS.map((tag, i) => (
                  <button
                    key={tag}
                    onClick={() => handleTagWord(tag)}
                    disabled={tagLoading}
                    className={clsx(
                      "tag-option text-sm",
                      currentWordTag === tag && "active",
                    )}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "1.25rem",
                        height: "1.25rem",
                        borderRadius: "4px",
                        background:
                          currentWordTag === tag
                            ? "rgba(255,255,255,0.3)"
                            : "#e2e8f0",
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        flexShrink: 0,
                      }}
                    >
                      {i + 1}
                    </span>
                    {TAG_LABELS[tag] || tag}
                  </button>
                ))}

                {currentWordTag && (
                  <button
                    onClick={handleClearTag}
                    disabled={tagLoading}
                    className="tag-option text-sm"
                    style={{
                      color: "#ef4444",
                      borderColor: "#fecaca",
                    }}
                  >
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.5rem",
                      }}
                    >
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "1.25rem",
                          height: "1.25rem",
                          borderRadius: "4px",
                          background: "#fee2e2",
                          fontSize: "0.6rem",
                          fontWeight: 700,
                        }}
                      >
                        ⌫
                      </span>
                      Clear
                    </span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Keyboard hints */}
          <div
            className="flex flex-wrap justify-center gap-4 mt-6"
            style={{ color: "var(--text-muted)" }}
          >
            {[
              { keys: "← →", label: "Select word" },
              { keys: "1-" + AVAILABLE_TAGS.length, label: "Tag" },
              { keys: "⌫", label: "Clear tag" },
              { keys: "↵", label: "Next sentence" },
            ].map(({ keys, label }) => (
              <div key={keys} className="flex items-center gap-2 text-xs">
                <kbd
                  style={{
                    padding: "0.125rem 0.375rem",
                    borderRadius: "4px",
                    background: "#f1f5f9",
                    border: "1px solid var(--border)",
                    fontFamily: "monospace",
                    fontSize: "0.7rem",
                    fontWeight: 600,
                  }}
                >
                  {keys}
                </kbd>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
