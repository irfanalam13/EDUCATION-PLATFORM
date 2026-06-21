"use client";

import * as React from "react";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";

export function ContentFilters({
  initialSearch = "",
  onChange,
}: {
  initialSearch?: string;
  onChange: (v: { search?: string }) => void;
}) {
  const [search, setSearch] = React.useState(initialSearch);

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search content..." />
      <div className="flex gap-2">
        <Button onClick={() => onChange({ search })}>Search</Button>
        <Button variant="secondary" onClick={() => { setSearch(""); onChange({ search: "" }); }}>
          Reset
        </Button>
      </div>
    </div>
  );
}
