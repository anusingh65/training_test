"use client";

import { Package, Truck, Building2, Store, ExternalLink } from "lucide-react";

interface CustodyEvent {
  id: string;
  from_entity: string | null;
  to_entity: string;
  event_type: string;
  location: string;
  timestamp: string;
  blockchain_tx_hash?: string;
}

const eventIcons: Record<string, React.ReactNode> = {
  manufactured: <Package size={16} />,
  shipped: <Truck size={16} />,
  received: <Building2 size={16} />,
  delivered: <Store size={16} />,
};

const eventColors: Record<string, { bg: string; border: string; text: string }> = {
  manufactured: { bg: "bg-primary-50", border: "border-primary", text: "text-primary" },
  shipped: { bg: "bg-warning-light", border: "border-warning", text: "text-warning" },
  received: { bg: "bg-success-light", border: "border-success", text: "text-success" },
  delivered: { bg: "bg-violet-50", border: "border-violet-500", text: "text-violet-500" },
};

export default function SupplyChainTimeline({
  events,
}: {
  events: CustodyEvent[];
}) {
  return (
    <div className="relative">
      <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />
      {events.map((event, i) => {
        const colors = eventColors[event.event_type] || { bg: "bg-gray-50", border: "border-border", text: "text-primary" };
        return (
          <div
            key={event.id}
            className="relative flex gap-4 pb-8 last:pb-0 animate-fade-in"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-2 shrink-0 ${colors.bg} ${colors.border} ${colors.text}`}>
              {eventIcons[event.event_type] || <Package size={16} />}
            </div>
            <div className="pt-1 flex-1">
              <p className="font-medium text-sm text-foreground capitalize">
                {event.event_type}
              </p>
              <p className="text-xs text-text-secondary mt-1">
                <span className="text-foreground">{event.to_entity}</span>
                {event.location && <span className="text-text-tertiary"> — {event.location}</span>}
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                {new Date(event.timestamp).toLocaleString()}
              </p>
              {event.blockchain_tx_hash && (
                <a
                  href={`https://amoy.polygonscan.com/tx/${event.blockchain_tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-1.5"
                >
                  <ExternalLink size={10} />
                  Polygonscan
                </a>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
