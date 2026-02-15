import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Tag as TagIcon } from "lucide-react";
import clsx from "clsx";
import SearchForm from "../components/SearchForm";
import SentenceCard from "../components/SentenceCard";
import Pagination from "../components/Pagination";
import { SearchResult, Filters, ActiveWord } from "../types";

const PAGE_SIZE = 10;

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [taggingMode, setTaggingMode] = useState(false);
  const [activeWord, setActiveWord] = useState<ActiveWord | null>(null);

  // Sync state from URL
  const query = searchParams.get("q") || "";
  const [localQuery, setLocalQuery] = useState(query);

  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  const page = parseInt(searchParams.get("page") || "1");
  const filters: Filters = {
    use_lemma: searchParams.get("use_lemma") === "true",
    is_hypothetical: searchParams.get("is_hypothetical") === "true",
    is_command: searchParams.get("is_command") === "true",
    is_time_clause: searchParams.get("is_time_clause") === "true",
    untagged_only: searchParams.get("untagged_only") === "true",
    subclause_types: searchParams.getAll("subclause_types"),
    tag: searchParams.get("tag") || "",
  };

  const updateSearchParams = (
    newQuery: string,
    newFilters: Filters,
    newPage: number,
  ) => {
    const params = new URLSearchParams();
    if (newQuery) params.set("q", newQuery);
    if (newFilters.use_lemma) params.set("use_lemma", "true");
    if (newFilters.is_hypothetical) params.set("is_hypothetical", "true");
    if (newFilters.is_command) params.set("is_command", "true");
    if (newFilters.is_time_clause) params.set("is_time_clause", "true");
    if (newFilters.untagged_only) params.set("untagged_only", "true");
    if (newFilters.tag) params.set("tag", newFilters.tag);
    newFilters.subclause_types.forEach((t) =>
      params.append("subclause_types", t),
    );
    if (newPage > 1) params.set("page", String(newPage));

    setSearchParams(params);
  };

  const performSearch = useCallback(async () => {
    if (
      !query &&
      !filters.is_command &&
      !filters.is_hypothetical &&
      !filters.is_time_clause &&
      !filters.tag &&
      !filters.untagged_only &&
      filters.subclause_types.length === 0
    )
      return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: query,
        limit: String(PAGE_SIZE),
        offset: String((page - 1) * PAGE_SIZE),
        use_lemma: String(filters.use_lemma),
        is_hypothetical: String(filters.is_hypothetical),
        is_command: String(filters.is_command),
        is_time_clause: String(filters.is_time_clause),
        untagged_only: String(filters.untagged_only),
      });

      if (filters.tag) params.append("tag", filters.tag);
      filters.subclause_types.forEach((t) =>
        params.append("subclause_types", t),
      );

      const res = await fetch(`/api/search?${params}`);
      const data = await res.json();
      setResults(data.data || []);
      setTotalCount(data.meta?.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [query, page, JSON.stringify(filters)]);

  useEffect(() => {
    performSearch();
  }, [performSearch]);

  const handleTagUpdated = (
    sentenceId: string,
    wordIndex: number,
    tag: string | null,
  ) => {
    setResults((prev) =>
      prev.map((r) => {
        if (r.ref_id === sentenceId) {
          const newTags = [...(r.tags || [])];
          const existingIdx = newTags.findIndex(
            (t) => t.word_index === wordIndex,
          );
          if (existingIdx >= 0) {
            if (tag === null) {
              newTags.splice(existingIdx, 1);
            } else {
              newTags[existingIdx] = { word_index: wordIndex, tag };
            }
          } else if (tag !== null) {
            newTags.push({ word_index: wordIndex, tag });
          }
          return { ...r, tags: newTags };
        }
        return r;
      }),
    );
  };

  return (
    <div className="container py-8">
      <SearchForm
        query={localQuery}
        setQuery={setLocalQuery}
        filters={filters}
        setFilters={(f) => updateSearchParams(localQuery, f, 1)}
        loading={loading}
        onSearch={() => updateSearchParams(localQuery, filters, 1)}
      />

      <main>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">
            {totalCount > 0
              ? `Results (${totalCount})`
              : loading
                ? "Searching..."
                : "Enter a search to begin"}
          </h2>
          <button
            onClick={() => {
              setTaggingMode(!taggingMode);
              setActiveWord(null);
            }}
            className={clsx(
              "btn flex items-center gap-2",
              taggingMode ? "btn-primary" : "bg-slate-200",
            )}
          >
            <TagIcon size={18} />
            {taggingMode ? "Tagging Mode: ON" : "Enable Tagging"}
          </button>
        </div>

        <div className="grid gap-6">
          {results.map((r) => (
            <SentenceCard
              key={r.ref_id}
              result={r}
              taggingMode={taggingMode}
              onWordClick={setActiveWord}
              activeWordIndex={
                activeWord?.sentenceId === r.ref_id
                  ? activeWord.wordIndex
                  : undefined
              }
              onTagSelected={(tag) => {
                if (activeWord) {
                  handleTagUpdated(
                    activeWord.sentenceId,
                    activeWord.wordIndex,
                    tag,
                  );
                  setActiveWord(null);
                }
              }}
            />
          ))}
        </div>

        {totalCount > PAGE_SIZE && (
          <Pagination
            currentPage={page}
            totalCount={totalCount}
            pageSize={PAGE_SIZE}
            onPageChange={(p) => updateSearchParams(query, filters, p)}
          />
        )}
      </main>
    </div>
  );
}
