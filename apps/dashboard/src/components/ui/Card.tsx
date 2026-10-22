interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
  hover?: boolean;
}

const paddingMap = {
  sm: "p-4",
  md: "p-6",
  lg: "p-8",
};

export default function Card({ children, className = "", padding = "md", hover = false }: CardProps) {
  return (
    <div
      className={`bg-white border border-border rounded-lg shadow-card ${paddingMap[padding]} ${
        hover ? "hover:shadow-card-hover transition-shadow" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}
