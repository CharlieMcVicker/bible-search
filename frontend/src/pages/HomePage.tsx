import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchForm from "../components/SearchForm";
import { Filters } from "../types";

export default function HomePage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<Filters>({
    use_lemma: false,
    is_hypothetical: false,
    is_command: false,
    is_time_clause: false,
    untagged_only: false,
    subclause_types: [],
    tag: "",
  });

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (filters.use_lemma) params.set("use_lemma", "true");
    if (filters.is_hypothetical) params.set("is_hypothetical", "true");
    if (filters.is_command) params.set("is_command", "true");
    if (filters.is_time_clause) params.set("is_time_clause", "true");
    if (filters.untagged_only) params.set("untagged_only", "true");
    if (filters.tag) params.set("tag", filters.tag);
    filters.subclause_types.forEach((t) => params.append("subclause_types", t));

    navigate(`/search?${params.toString()}`);
  };

  return (
    <div className="container py-24">
      <SearchForm
        query={query}
        setQuery={setQuery}
        filters={filters}
        setFilters={setFilters}
        loading={false}
        onSearch={handleSearch}
      />

      <div className="max-w-2xl mx-auto mt-12 text-center text-slate-500">
        <p className="text-lg">
          Explore the Cherokee language through a searchable corpus of
          sentences. Find specific grammatical structures, vocabulary, and more.
        </p>
      </div>
    </div>
  );
}
