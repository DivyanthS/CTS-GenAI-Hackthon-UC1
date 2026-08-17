import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

export type RGB = [number, number, number];

export const PDF_COLORS = {
  navy: [24, 38, 58] as RGB,
  primary: [26, 88, 158] as RGB,
  primarySoft: [232, 240, 249] as RGB,
  text: [26, 32, 41] as RGB,
  muted: [110, 122, 138] as RGB,
  line: [219, 226, 234] as RGB,
  surface: [246, 249, 252] as RGB,
  white: [255, 255, 255] as RGB,
  critical: [178, 38, 30] as RGB,
  criticalSoft: [252, 234, 233] as RGB,
  high: [186, 104, 12] as RGB,
  highSoft: [253, 241, 226] as RGB,
  medium: [152, 130, 20] as RGB,
  mediumSoft: [250, 247, 226] as RGB,
  low: [22, 118, 86] as RGB,
  lowSoft: [230, 245, 239] as RGB,
};

export function riskColors(level: string): { fg: RGB; bg: RGB } {
  switch (level.toLowerCase()) {
    case "critical":
      return { fg: PDF_COLORS.critical, bg: PDF_COLORS.criticalSoft };
    case "high":
      return { fg: PDF_COLORS.high, bg: PDF_COLORS.highSoft };
    case "medium":
      return { fg: PDF_COLORS.medium, bg: PDF_COLORS.mediumSoft };
    default:
      return { fg: PDF_COLORS.low, bg: PDF_COLORS.lowSoft };
  }
}

export const currency = (v: number) =>
  `$${Math.round(v).toLocaleString("en-US")}`;
export const num = (v: number) => v.toLocaleString("en-US");

export interface DocContext {
  reportTitle: string;
  reportId: string;
  generatedAt: Date;
}

const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN = 16;
const CONTENT_W = PAGE_W - MARGIN * 2;
const BODY_TOP = 30;
const BODY_BOTTOM = PAGE_H - 18;

/**
 * Thin, opinionated wrapper around jsPDF that renders the FraudGuard AI
 * report design language: cover page, running header/footer, sections,
 * KPI cards, tables, risk panels, evidence blocks, timelines and bar charts.
 */
export class ReportDoc {
  readonly doc: jsPDF;
  private y = BODY_TOP;
  private hasCover = false;

  constructor(private readonly ctx: DocContext) {
    this.doc = new jsPDF({ unit: "mm", format: "a4", compress: true });
    this.doc.setFont("helvetica", "normal");
  }

  // ---------------------------------------------------------------- layout

  get cursor() {
    return this.y;
  }

  private setFill(c: RGB) {
    this.doc.setFillColor(c[0], c[1], c[2]);
  }
  private setDraw(c: RGB) {
    this.doc.setDrawColor(c[0], c[1], c[2]);
  }
  private setText(c: RGB) {
    this.doc.setTextColor(c[0], c[1], c[2]);
  }

  private font(size: number, style: "normal" | "bold" | "italic" = "normal", color: RGB = PDF_COLORS.text) {
    this.doc.setFont("helvetica", style);
    this.doc.setFontSize(size);
    this.setText(color);
  }

  newPage() {
    this.doc.addPage();
    this.y = BODY_TOP;
  }

  /** Adds a page when `height` mm would not fit on the current page. */
  ensure(height: number) {
    if (this.y + height > BODY_BOTTOM) this.newPage();
  }

  space(mm = 6) {
    this.y += mm;
  }

  // ----------------------------------------------------------------- cover

  cover(opts: {
    reportType: string;
    facts: { label: string; value: string }[];
    preparedFor: string;
    riskHighlight?: { score: number; level: string } | undefined;
  }) {
    this.hasCover = true;
    const d = this.doc;

    this.setFill(PDF_COLORS.navy);
    d.rect(0, 0, PAGE_W, 96, "F");

    this.font(9, "bold", PDF_COLORS.white);
    d.setCharSpace(1.6);
    d.text("FRAUDGUARD AI", MARGIN, 34);
    d.setCharSpace(0);
    this.font(9, "normal", [176, 190, 208]);
    d.text("Claims Payment Integrity Platform", MARGIN, 41);

    this.setDraw([70, 88, 112]);
    d.setLineWidth(0.3);
    d.line(MARGIN, 50, PAGE_W - MARGIN, 50);

    this.font(24, "bold", PDF_COLORS.white);
    const titleLines = d.splitTextToSize(opts.reportType, CONTENT_W) as string[];
    d.text(titleLines, MARGIN, 64);

    this.font(9, "normal", [176, 190, 208]);
    d.text("CONFIDENTIAL — FOR AUTHORIZED USE ONLY", MARGIN, 88);

    let y = 118;
    if (opts.riskHighlight) {
      const { fg, bg } = riskColors(opts.riskHighlight.level);
      this.setFill(bg);
      d.roundedRect(MARGIN, y, CONTENT_W, 26, 2, 2, "F");
      this.setFill(fg);
      d.rect(MARGIN, y, 1.6, 26, "F");
      this.font(20, "bold", fg);
      d.text(`${opts.riskHighlight.score}%`, MARGIN + 8, y + 17);
      this.font(11, "bold", fg);
      d.text(opts.riskHighlight.level.toUpperCase(), MARGIN + 34, y + 13);
      this.font(8.5, "normal", PDF_COLORS.muted);
      d.text("Model risk signal — not a determination of fraud", MARGIN + 34, y + 19);
      y += 36;
    }

    for (const fact of opts.facts) {
      this.font(8, "bold", PDF_COLORS.muted);
      d.setCharSpace(0.8);
      d.text(fact.label.toUpperCase(), MARGIN, y);
      d.setCharSpace(0);
      this.font(11, "bold", PDF_COLORS.text);
      d.text(fact.value, MARGIN + 58, y);
      this.setDraw(PDF_COLORS.line);
      d.setLineWidth(0.2);
      d.line(MARGIN, y + 3.6, PAGE_W - MARGIN, y + 3.6);
      y += 11;
    }

    y = Math.max(y + 8, 236);
    this.font(8, "bold", PDF_COLORS.muted);
    d.text("PREPARED FOR", MARGIN, y);
    this.font(10, "normal", PDF_COLORS.text);
    d.text(opts.preparedFor, MARGIN, y + 6);

    this.font(8, "bold", PDF_COLORS.muted);
    d.text("REPORT ID", MARGIN, y + 18);
    this.font(10, "normal", PDF_COLORS.text);
    d.text(this.ctx.reportId, MARGIN, y + 24);

    this.font(8, "bold", PDF_COLORS.muted);
    d.text("GENERATED", PAGE_W / 2, y + 18);
    this.font(10, "normal", PDF_COLORS.text);
    d.text(formatDateTime(this.ctx.generatedAt), PAGE_W / 2, y + 24);

    this.newPage();
  }

  // -------------------------------------------------------------- sections

  section(title: string, subtitle?: string) {
    // Keep the heading with at least a block of following content.
    this.ensure(34);
    const d = this.doc;
    this.setFill(PDF_COLORS.primary);
    d.rect(MARGIN, this.y - 3.4, 2.2, 7, "F");
    this.font(12, "bold", PDF_COLORS.navy);
    d.text(title, MARGIN + 6, this.y + 2);
    this.y += 6;
    if (subtitle) {
      this.font(8.5, "normal", PDF_COLORS.muted);
      const lines = d.splitTextToSize(subtitle, CONTENT_W - 6) as string[];
      d.text(lines, MARGIN + 6, this.y + 2);
      this.y += lines.length * 4 + 1;
    }
    this.setDraw(PDF_COLORS.line);
    d.setLineWidth(0.2);
    d.line(MARGIN, this.y + 1.5, PAGE_W - MARGIN, this.y + 1.5);
    this.y += 7;
  }

  subheading(text: string) {
    this.ensure(16);
    this.font(9.5, "bold", PDF_COLORS.text);
    this.doc.text(text, MARGIN, this.y);
    this.y += 5;
  }

  para(text: string, opts: { italic?: boolean; muted?: boolean; size?: number } = {}) {
    const size = opts.size ?? 9.5;
    this.font(size, opts.italic ? "italic" : "normal", opts.muted ? PDF_COLORS.muted : PDF_COLORS.text);
    const lines = this.doc.splitTextToSize(text, CONTENT_W) as string[];
    for (const line of lines) {
      this.ensure(6);
      this.font(size, opts.italic ? "italic" : "normal", opts.muted ? PDF_COLORS.muted : PDF_COLORS.text);
      this.doc.text(line, MARGIN, this.y);
      this.y += size * 0.52;
    }
    this.y += 3;
  }

  bullets(items: string[]) {
    for (const item of items) {
      const lines = this.doc.splitTextToSize(item, CONTENT_W - 6) as string[];
      this.ensure(lines.length * 5 + 2);
      this.font(9.5, "normal", PDF_COLORS.primary);
      this.doc.text("•", MARGIN, this.y);
      this.font(9.5, "normal", PDF_COLORS.text);
      this.doc.text(lines, MARGIN + 5, this.y);
      this.y += lines.length * 4.8 + 2;
    }
    this.y += 2;
  }

  keyValues(pairs: { label: string; value: string }[], cols = 3) {
    const colW = CONTENT_W / cols;
    let i = 0;
    while (i < pairs.length) {
      const row = pairs.slice(i, i + cols);
      const heights = row.map(
        (p) => (this.doc.splitTextToSize(p.value || "—", colW - 6) as string[]).length,
      );
      const rowH = 8 + Math.max(...heights) * 4.4;
      this.ensure(rowH + 2);
      row.forEach((p, c) => {
        const x = MARGIN + c * colW;
        this.font(7.5, "bold", PDF_COLORS.muted);
        this.doc.text(p.label.toUpperCase(), x, this.y);
        this.font(9.5, "normal", PDF_COLORS.text);
        const lines = this.doc.splitTextToSize(p.value || "—", colW - 6) as string[];
        this.doc.text(lines, x, this.y + 5);
      });
      this.y += rowH;
      i += cols;
    }
    this.y += 2;
  }

  kpis(items: { label: string; value: string; tone?: string }[], cols = 4) {
    const gap = 4;
    const cardW = (CONTENT_W - gap * (cols - 1)) / cols;
    for (let i = 0; i < items.length; i += cols) {
      const row = items.slice(i, i + cols);
      this.ensure(24);
      row.forEach((item, c) => {
        const x = MARGIN + c * (cardW + gap);
        const tone = item.tone ? riskColors(item.tone) : null;
        this.setFill(tone ? tone.bg : PDF_COLORS.surface);
        this.setDraw(PDF_COLORS.line);
        this.doc.setLineWidth(0.2);
        this.doc.roundedRect(x, this.y, cardW, 20, 1.6, 1.6, "FD");
        this.font(7.5, "bold", PDF_COLORS.muted);
        this.doc.text(
          (this.doc.splitTextToSize(item.label.toUpperCase(), cardW - 6) as string[])[0]!,
          x + 3.5,
          this.y + 6.5,
        );
        this.font(13, "bold", tone ? tone.fg : PDF_COLORS.navy);
        this.doc.text(item.value, x + 3.5, this.y + 15);
      });
      this.y += 24;
    }
    this.y += 2;
  }

  riskPanel(score: number, level: string, prediction: string, caption?: string) {
    this.ensure(34);
    const { fg, bg } = riskColors(level);
    const d = this.doc;
    this.setFill(bg);
    d.roundedRect(MARGIN, this.y, CONTENT_W, 28, 2, 2, "F");
    this.setFill(fg);
    d.rect(MARGIN, this.y, 2, 28, "F");

    this.font(26, "bold", fg);
    d.text(`${score}%`, MARGIN + 8, this.y + 19);

    const x = MARGIN + 46;
    this.font(7.5, "bold", PDF_COLORS.muted);
    d.text("RISK LEVEL", x, this.y + 9);
    d.text("MODEL PREDICTION", x + 44, this.y + 9);
    this.font(11, "bold", fg);
    d.text(level.toUpperCase(), x, this.y + 16);
    this.font(11, "bold", PDF_COLORS.navy);
    d.text(prediction, x + 44, this.y + 16);
    this.font(7.5, "normal", PDF_COLORS.muted);
    d.text(
      caption ?? "Model-generated risk signal. Not a determination of fraud.",
      x,
      this.y + 23,
    );
    this.y += 34;
  }

  callout(title: string, body: string, tone: "info" | "warning" | "neutral" = "info") {
    const bg =
      tone === "warning" ? PDF_COLORS.highSoft : tone === "neutral" ? PDF_COLORS.surface : PDF_COLORS.primarySoft;
    const fg =
      tone === "warning" ? PDF_COLORS.high : tone === "neutral" ? PDF_COLORS.muted : PDF_COLORS.primary;
    this.font(9, "normal", PDF_COLORS.text);
    const lines = this.doc.splitTextToSize(body, CONTENT_W - 12) as string[];
    const h = 12 + lines.length * 4.4;
    this.ensure(h + 4);
    this.setFill(bg);
    this.doc.roundedRect(MARGIN, this.y, CONTENT_W, h, 1.6, 1.6, "F");
    this.setFill(fg);
    this.doc.rect(MARGIN, this.y, 1.6, h, "F");
    this.font(8, "bold", fg);
    this.doc.text(title.toUpperCase(), MARGIN + 6, this.y + 6.5);
    this.font(9, "normal", PDF_COLORS.text);
    this.doc.text(lines, MARGIN + 6, this.y + 12);
    this.y += h + 6;
  }

  table(head: string[], body: (string | number)[][], opts: { widths?: Record<number, number> } = {}) {
    if (!body.length) {
      this.para("No records match this selection.", { italic: true, muted: true });
      return;
    }
    const columnStyles: Record<number, { cellWidth: number }> = {};
    Object.entries(opts.widths ?? {}).forEach(([k, v]) => {
      columnStyles[Number(k)] = { cellWidth: v };
    });

    autoTable(this.doc, {
      head: [head],
      body: body.map((r) => r.map((c) => String(c))),
      startY: this.y,
      margin: { left: MARGIN, right: MARGIN, top: BODY_TOP, bottom: 18 },
      theme: "grid",
      styles: {
        font: "helvetica",
        fontSize: 8,
        cellPadding: 2.2,
        lineColor: PDF_COLORS.line,
        lineWidth: 0.15,
        textColor: PDF_COLORS.text,
        overflow: "linebreak",
      },
      headStyles: {
        fillColor: PDF_COLORS.navy,
        textColor: PDF_COLORS.white,
        fontStyle: "bold",
        fontSize: 8,
      },
      alternateRowStyles: { fillColor: [249, 251, 253] },
      columnStyles,
      rowPageBreak: "avoid",
    });
    // @ts-expect-error lastAutoTable is attached by jspdf-autotable
    this.y = (this.doc.lastAutoTable?.finalY ?? this.y) + 8;
  }

  bars(items: { label: string; value: number; display?: string; tone?: string }[]) {
    const max = Math.max(...items.map((i) => i.value), 1);
    const labelW = 58;
    const barW = CONTENT_W - labelW - 30;
    for (const item of items) {
      this.ensure(9);
      this.font(8.5, "normal", PDF_COLORS.text);
      this.doc.text(
        (this.doc.splitTextToSize(item.label, labelW - 3) as string[])[0]!,
        MARGIN,
        this.y + 3,
      );
      this.setFill(PDF_COLORS.surface);
      this.doc.roundedRect(MARGIN + labelW, this.y, barW, 4.4, 1, 1, "F");
      const w = Math.max((item.value / max) * barW, 1.5);
      const tone = item.tone ? riskColors(item.tone).fg : PDF_COLORS.primary;
      this.setFill(tone);
      this.doc.roundedRect(MARGIN + labelW, this.y, w, 4.4, 1, 1, "F");
      this.font(8.5, "bold", PDF_COLORS.navy);
      this.doc.text(item.display ?? num(item.value), MARGIN + labelW + barW + 3, this.y + 3.6);
      this.y += 8;
    }
    this.y += 4;
  }

  timeline(items: { label: string; detail: string; state?: string; at?: string }[]) {
    for (const [i, item] of items.entries()) {
      const detailLines = this.doc.splitTextToSize(item.detail, CONTENT_W - 20) as string[];
      const h = 6 + detailLines.length * 4.2;
      this.ensure(h + 4);
      const done = (item.state ?? "done") === "done";
      const color = done ? PDF_COLORS.primary : PDF_COLORS.line;
      this.setFill(color);
      this.doc.circle(MARGIN + 2, this.y - 1, 1.6, "F");
      if (i < items.length - 1) {
        this.setDraw(PDF_COLORS.line);
        this.doc.setLineWidth(0.3);
        this.doc.line(MARGIN + 2, this.y + 1, MARGIN + 2, this.y + h + 1);
      }
      this.font(9, "bold", done ? PDF_COLORS.navy : PDF_COLORS.muted);
      this.doc.text(item.label, MARGIN + 8, this.y);
      if (item.at) {
        this.font(8, "normal", PDF_COLORS.muted);
        this.doc.text(item.at, PAGE_W - MARGIN, this.y, { align: "right" });
      }
      this.font(8.5, "normal", PDF_COLORS.muted);
      this.doc.text(detailLines, MARGIN + 8, this.y + 4.4);
      this.y += h + 3;
    }
    this.y += 2;
  }

  disclaimer(text: string) {
    this.ensure(26);
    const lines = this.doc.splitTextToSize(text, CONTENT_W - 10) as string[];
    const h = 10 + lines.length * 4.2;
    this.setFill(PDF_COLORS.surface);
    this.setDraw(PDF_COLORS.line);
    this.doc.setLineWidth(0.2);
    this.doc.roundedRect(MARGIN, this.y, CONTENT_W, h, 1.6, 1.6, "FD");
    this.font(7.5, "bold", PDF_COLORS.muted);
    this.doc.text("DISCLAIMER", MARGIN + 5, this.y + 6);
    this.font(8.5, "italic", PDF_COLORS.text);
    this.doc.text(lines, MARGIN + 5, this.y + 11);
    this.y += h + 6;
  }

  // -------------------------------------------------------------- finalize

  finalize(): { blob: Blob; pageCount: number } {
    const d = this.doc;
    const pages = d.getNumberOfPages();
    for (let p = 1; p <= pages; p++) {
      d.setPage(p);
      const isCover = this.hasCover && p === 1;
      if (!isCover) {
        // Running header
        this.setFill(PDF_COLORS.navy);
        d.rect(0, 0, PAGE_W, 16, "F");
        this.font(8, "bold", PDF_COLORS.white);
        d.setCharSpace(0.8);
        d.text("FRAUDGUARD AI", MARGIN, 7.5);
        d.setCharSpace(0);
        this.font(7, "normal", [176, 190, 208]);
        d.text("Claims Payment Integrity", MARGIN, 12);
        this.font(8, "bold", PDF_COLORS.white);
        d.text(this.ctx.reportTitle, PAGE_W - MARGIN, 7.5, { align: "right" });
        this.font(7, "normal", [176, 190, 208]);
        d.text(
          `${this.ctx.reportId}  ·  ${formatDateTime(this.ctx.generatedAt)}`,
          PAGE_W - MARGIN,
          12,
          { align: "right" },
        );
      }
      // Footer
      this.setDraw(PDF_COLORS.line);
      d.setLineWidth(0.2);
      d.line(MARGIN, PAGE_H - 12, PAGE_W - MARGIN, PAGE_H - 12);
      this.font(7.5, "normal", PDF_COLORS.muted);
      d.text("FraudGuard AI — Confidential — For Authorized Use Only", MARGIN, PAGE_H - 7.5);
      d.text(`Page ${p} of ${pages}`, PAGE_W - MARGIN, PAGE_H - 7.5, { align: "right" });
    }
    return { blob: d.output("blob") as Blob, pageCount: pages };
  }
}

export function formatDateTime(date: Date) {
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(date: Date) {
  return date.toISOString().slice(0, 10);
}
