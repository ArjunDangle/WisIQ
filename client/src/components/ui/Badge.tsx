import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "amber" | "teal" | "blue" | "outline";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-primary text-primary-foreground",
    amber: "bg-accent-amber-bg text-accent-amber border border-accent-amber/20",
    teal: "bg-accent-teal-bg text-accent-teal border border-accent-teal/20",
    blue: "bg-accent-blue-bg text-accent-blue border border-accent-blue/20",
    outline: "text-foreground border border-border",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
