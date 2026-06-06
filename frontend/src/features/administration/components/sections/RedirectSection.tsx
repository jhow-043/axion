import { useNavigate } from "react-router";
import { ExternalLink } from "lucide-react";

interface RedirectSectionProps {
  title: string;
  description: string;
  links: { label: string; to: string }[];
}

export function RedirectSection({ title, description, links }: RedirectSectionProps) {
  const navigate = useNavigate();

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="text-sm text-gray-600">{description}</p>
      <div className="flex flex-col gap-2">
        {links.map(({ label, to }) => (
          <button
            key={to}
            onClick={() => void navigate(to)}
            className="flex items-center gap-2 w-fit px-4 py-2 border rounded hover:bg-gray-50 text-sm transition"
          >
            <ExternalLink className="h-4 w-4 text-gray-500" />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
