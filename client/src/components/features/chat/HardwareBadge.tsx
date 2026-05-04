import { motion } from "framer-motion";
import { Badge } from "@/components/ui/Badge";
import { BrainCircuit, Cpu } from "lucide-react";

interface HardwareBadgeProps {
  intent?: string;
  hardware?: string[];
}

export function HardwareBadge({ intent, hardware }: HardwareBadgeProps) {
  if (!intent && (!hardware || hardware.length === 0)) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      className="flex flex-wrap gap-2 mb-3"
    >
      {intent && (
        <Badge variant="teal" className="gap-1 px-3 py-1">
          <BrainCircuit className="w-3.5 h-3.5" />
          <span className="capitalize tracking-wide font-medium">{intent.replace(/_/g, " ")}</span>
        </Badge>
      )}
      
      {hardware && hardware.map((hw, idx) => (
        <Badge key={idx} variant="outline" className="gap-1 px-3 py-1 bg-white/50 dark:bg-black/50 backdrop-blur-sm">
          <Cpu className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="tracking-wide uppercase font-semibold text-[10px] text-muted-foreground">{hw}</span>
        </Badge>
      ))}
    </motion.div>
  );
}
