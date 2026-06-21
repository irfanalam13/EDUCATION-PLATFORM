import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t mt-12">
      <div className="mx-auto max-w-6xl px-4 py-10 flex flex-col sm:flex-row gap-6 sm:items-center sm:justify-between">
        <div className="text-sm">
          <div className="font-medium">Edu Platform</div>
          <div className="opacity-70">Academics curriculum browsing (Levels → Topics).</div>
        </div>

        <div className="flex flex-wrap gap-3 text-sm">
          <Link className="underline opacity-80 hover:opacity-100" href="/academics">
            Academics
          </Link>
          <Link className="underline opacity-80 hover:opacity-100" href="/academics/levels">
            Levels
          </Link>
        </div>
      </div>
    </footer>
  );
}
