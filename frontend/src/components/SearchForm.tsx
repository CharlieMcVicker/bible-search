import React from "react";
import { Search, Loader2 } from "lucide-react";
import { Filters } from "../types";

const AVAILABLE_TAGS = [
  "converb",
  "yi+converb",
  "yi+present",
  "incompletive deverbal",
  "completive deverbal",
];

interface SearchFormProps {
  query: string;
  setQuery: (query: string) => void;
  filters: Filters;
  setFilters: (filters: Filters) => void;
  loading: boolean;
  onSearch: (e?: React.FormEvent) => void;
}

export default function SearchForm({
  query,
  setQuery,
  filters,
  setFilters,
  loading,
  onSearch,
}: SearchFormProps) {
  const toggleFilter = (
    key: keyof Omit<Filters, "subclause_types" | "tag">,
  ) => {
    setFilters({ ...filters, [key]: !filters[key] });
  };

  return (
    <header className="text-center mb-12">
      <h1 className="text-4xl font-bold mb-4">Cherokee Search</h1>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSearch(e);
        }}
        className="max-w-2xl mx-auto flex gap-2"
      >
        <input
          className="input"
          placeholder="Search Cherokee sentences..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary flex items-center gap-2"
        >
          {loading ? (
            <Loader2 className="animate-spin" />
          ) : (
            <Search size={20} />
          )}
          Search
        </button>
      </form>

      <div className="flex flex-wrap justify-center items-center gap-6 mt-6">
        <div className="flex flex-wrap gap-4">
          {(
            [
              "use_lemma",
              "is_hypothetical",
              "is_command",
              "is_time_clause",
              "untagged_only",
            ] as const
          ).map((f) => (
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
          ))}
        </div>

        <div className="h-6 w-px bg-slate-200 hidden sm:block"></div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-slate-400 uppercase tracking-tight">
            Filter by Tag:
          </span>
          <select
            className="select text-sm py-1"
            value={filters.tag}
            onChange={(e) => setFilters({ ...filters, tag: e.target.value })}
          >
            <option value="">All Tags</option>
            {AVAILABLE_TAGS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
