"use client";
import { useRef, useEffect, useState } from "react";
import { Typography, Box, Paper } from "@mui/material";
import { Dependency } from "@/lib/tech-catalogue-types";

interface Props {
  appKey: string;
  appName: string;
  upstream: Dependency[];
  downstream: Dependency[];
}

// ── C4 styles (from drawio-c4izr) ────────────────────────────────────
const C4_SYSTEM_STYLE =
  "rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor=#1061B0;fontColor=#ffffff;align=center;arcSize=10;strokeColor=#0D5091;metaEdit=1;resizable=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];";
const C4_EXTERNAL_STYLE =
  "rounded=1;whiteSpace=wrap;html=1;labelBackgroundColor=none;fillColor=#8C8496;fontColor=#ffffff;align=center;arcSize=10;strokeColor=#736782;metaEdit=1;resizable=0;points=[[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];";
const C4_EDGE_STYLE =
  "endArrow=blockThin;html=1;fontSize=10;fontColor=#404040;strokeWidth=1;endFill=1;strokeColor=#828282;elbow=vertical;metaEdit=1;endSize=14;startSize=14;jumpStyle=arc;jumpSize=16;rounded=0;edgeStyle=orthogonalEdgeStyle;";

const BOX_W = 240;
const BOX_H = 120;
const H_GAP = 100;
const V_GAP = 40;

// ── XML helpers ───────────────────────────────────────────────────────
function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function c4Label(name: string, type: string, desc: string): string {
  return (
    `<font style="font-size: 16px"><b>${escapeXml(name)}</b></font>` +
    `<div>[${escapeXml(type)}]</div><br>` +
    `<div><font style="font-size: 11px"><font color="#cccccc">${escapeXml(desc)}</font></font></div>`
  );
}

function edgeLabel(desc: string, tech: string): string {
  return (
    `<div style="text-align: left">` +
    `<div style="text-align: center"><b>${escapeXml(desc)}</b></div>` +
    `<div style="text-align: center">[${escapeXml(tech)}]</div></div>`
  );
}

// ── XML generation ────────────────────────────────────────────────────
function buildDiagramXml(
  appKey: string,
  appName: string,
  upstream: Dependency[],
  downstream: Dependency[]
): string {
  const cells: string[] = [];
  const ids = new Map<string, string>();
  let nextId = 2;

  function getId(key: string): string {
    if (!ids.has(key)) ids.set(key, String(nextId++));
    return ids.get(key)!;
  }

  const maxSide = Math.max(upstream.length, downstream.length, 1);
  const totalHeight = maxSide * (BOX_H + V_GAP) - V_GAP;

  // Center column — the main app
  const centerX = (upstream.length > 0 ? BOX_W + H_GAP : 0) + 20;
  const centerY = totalHeight / 2 - BOX_H / 2;
  const mainId = getId(appKey);

  cells.push(
    `<object id="${mainId}" placeholders="1" c4Name="${escapeXml(appName)}" c4Type="Software System" c4Description="Current system" label="${escapeXml(c4Label(appName, "Software System", "Current system"))}">` +
    `<mxCell style="${C4_SYSTEM_STYLE}" vertex="1" parent="1">` +
    `<mxGeometry x="${centerX}" y="${centerY}" width="${BOX_W}" height="${BOX_H}" as="geometry"/>` +
    `</mxCell></object>`
  );

  // Upstream (left column)
  const upX = 20;
  const upStartY = totalHeight / 2 - (upstream.length * (BOX_H + V_GAP) - V_GAP) / 2;
  upstream.forEach((dep, i) => {
    const id = getId(dep.app_key);
    const y = upStartY + i * (BOX_H + V_GAP);
    const desc = dep.notes || `${dep.type} dependency`;
    cells.push(
      `<object id="${id}" placeholders="1" c4Name="${escapeXml(dep.display_name)}" c4Type="Software System" c4Description="${escapeXml(desc)}" label="${escapeXml(c4Label(dep.display_name, "Software System", desc))}">` +
      `<mxCell style="${C4_EXTERNAL_STYLE}" vertex="1" parent="1">` +
      `<mxGeometry x="${upX}" y="${y}" width="${BOX_W}" height="${BOX_H}" as="geometry"/>` +
      `</mxCell></object>`
    );
    const edgeId = String(nextId++);
    cells.push(
      `<object id="${edgeId}" placeholders="1" c4Type="Relationship" c4Technology="${escapeXml(dep.protocol)}" c4Description="${escapeXml(dep.type)}" label="${escapeXml(edgeLabel(dep.type, dep.protocol))}">` +
      `<mxCell style="${C4_EDGE_STYLE}" edge="1" parent="1" source="${id}" target="${mainId}">` +
      `<mxGeometry relative="1" as="geometry"/>` +
      `</mxCell></object>`
    );
  });

  // Downstream (right column)
  const downX = centerX + BOX_W + H_GAP;
  const downStartY = totalHeight / 2 - (downstream.length * (BOX_H + V_GAP) - V_GAP) / 2;
  downstream.forEach((dep, i) => {
    const id = getId(dep.app_key);
    const y = downStartY + i * (BOX_H + V_GAP);
    const desc = dep.notes || `${dep.type} dependency`;
    cells.push(
      `<object id="${id}" placeholders="1" c4Name="${escapeXml(dep.display_name)}" c4Type="Software System" c4Description="${escapeXml(desc)}" label="${escapeXml(c4Label(dep.display_name, "Software System", desc))}">` +
      `<mxCell style="${C4_EXTERNAL_STYLE}" vertex="1" parent="1">` +
      `<mxGeometry x="${downX}" y="${y}" width="${BOX_W}" height="${BOX_H}" as="geometry"/>` +
      `</mxCell></object>`
    );
    const edgeId = String(nextId++);
    cells.push(
      `<object id="${edgeId}" placeholders="1" c4Type="Relationship" c4Technology="${escapeXml(dep.protocol)}" c4Description="${escapeXml(dep.type)}" label="${escapeXml(edgeLabel(dep.type, dep.protocol))}">` +
      `<mxCell style="${C4_EDGE_STYLE}" edge="1" parent="1" source="${mainId}" target="${id}">` +
      `<mxGeometry relative="1" as="geometry"/>` +
      `</mxCell></object>`
    );
  });

  return (
    `<mxGraphModel>` +
    `<root>` +
    `<mxCell id="0"/>` +
    `<mxCell id="1" parent="0"/>` +
    cells.join("") +
    `</root>` +
    `</mxGraphModel>`
  );
}

// ── Component ─────────────────────────────────────────────────────────
export default function DependencyDiagram({
  appKey,
  appName,
  upstream,
  downstream,
}: Props) {
  const viewerRef = useRef<HTMLIFrameElement>(null);
  const [viewerLoaded, setViewerLoaded] = useState(false);
  const xmlRef = useRef<string>("");

  useEffect(() => {
    xmlRef.current = buildDiagramXml(appKey, appName, upstream, downstream);
  }, [appKey, appName, upstream, downstream]);

  useEffect(() => {
    function handleMessage(evt: MessageEvent) {
      if (
        viewerRef.current?.contentWindow &&
        evt.source === viewerRef.current.contentWindow
      ) {
        let msg;
        try {
          msg = JSON.parse(evt.data);
        } catch {
          return;
        }
        if (msg.event === "init") {
          viewerRef.current.contentWindow.postMessage(
            JSON.stringify({ action: "load", xml: xmlRef.current, autosave: 0 }),
            "*"
          );
          setViewerLoaded(true);
        }
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const hasDeps = upstream.length > 0 || downstream.length > 0;

  if (!hasDeps) {
    return (
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
          Dependency Diagram
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No dependencies to display.
        </Typography>
      </Box>
    );
  }

  const maxSide = Math.max(upstream.length, downstream.length, 1);
  const diagramHeight = Math.max(300, maxSide * (BOX_H + V_GAP) + 80);

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" sx={{ mb: 1.5, color: "#022D5E" }}>
        Dependency Diagram
      </Typography>
      <Paper variant="outlined" sx={{ overflow: "hidden", position: "relative" }}>
        {!viewerLoaded && (
          <Box
            sx={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              bgcolor: "#f8f9fa",
              zIndex: 1,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              Loading diagram...
            </Typography>
          </Box>
        )}
        <iframe
          ref={viewerRef}
          src="https://embed.diagrams.net/?embed=1&proto=json&spin=1&chrome=0"
          style={{
            width: "100%",
            height: diagramHeight,
            border: "none",
            display: "block",
          }}
          title="C4 Dependency Diagram"
        />
      </Paper>
    </Box>
  );
}
