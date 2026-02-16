import { useState, useCallback, useEffect, useRef } from "react";

// ============================================================================
// VAELIX CITADEL PRIMITIVES — INTERACTIVE GATE ATLAS
// ============================================================================

// Gate logic functions (mirrors cells.v exactly)
const GATES = {
  buffer_cell: {
    name: "BUFFER",
    verilog: "assign out = in;",
    inputs: ["in"],
    desc: "Identity relay. Signal passes through unmodified.",
    fn: ({ in: a }) => ({ out: a }),
    category: "unary",
  },
  not_cell: {
    name: "NOT",
    verilog: "assign out = !in;",
    inputs: ["in"],
    desc: "Inverter. Flips the logic state.",
    fn: ({ in: a }) => ({ out: a ^ 1 }),
    category: "unary",
  },
  and_cell: {
    name: "AND",
    verilog: "assign out = a & b;",
    inputs: ["a", "b"],
    desc: "Conjunction. Output HIGH only when both inputs HIGH.",
    fn: ({ a, b }) => ({ out: a & b }),
    category: "binary",
  },
  or_cell: {
    name: "OR",
    verilog: "assign out = a | b;",
    inputs: ["a", "b"],
    desc: "Disjunction. Output HIGH when either input HIGH.",
    fn: ({ a, b }) => ({ out: a | b }),
    category: "binary",
  },
  xor_cell: {
    name: "XOR",
    verilog: "assign out = a ^ b;",
    inputs: ["a", "b"],
    desc: "Exclusive-OR. Output HIGH when inputs differ.",
    fn: ({ a, b }) => ({ out: a ^ b }),
    category: "binary",
  },
  nand_cell: {
    name: "NAND",
    verilog: "assign out = !(a&b);",
    inputs: ["a", "b"],
    desc: "Negated AND. Universal gate — can build any logic.",
    fn: ({ a, b }) => ({ out: (a & b) ^ 1 }),
    category: "binary",
  },
  nor_cell: {
    name: "NOR",
    verilog: "assign out = !(a|b);",
    inputs: ["a", "b"],
    desc: "Negated OR. Universal gate — can build any logic.",
    fn: ({ a, b }) => ({ out: (a | b) ^ 1 }),
    category: "binary",
  },
  xnor_cell: {
    name: "XNOR",
    verilog: "assign out = !(a^b);",
    inputs: ["a", "b"],
    desc: "Equivalence gate. Output HIGH when inputs match.",
    fn: ({ a, b }) => ({ out: (a ^ b) ^ 1 }),
    category: "binary",
  },
  mux_cell: {
    name: "MUX",
    verilog: "assign out = sel ? b : a;",
    inputs: ["a", "b", "sel"],
    desc: "2:1 Multiplexer. SEL chooses between A and B.",
    fn: ({ a, b, sel }) => ({ out: sel ? b : a }),
    category: "mux",
  },
  dff_cell: {
    name: "DFF",
    verilog: "always @(posedge clk) q <= d;",
    inputs: ["d"],
    desc: "D Flip-Flop. Captures D on rising clock edge.",
    fn: null,
    category: "sequential",
  },
  dffr_cell: {
    name: "DFF+R",
    verilog: "always @(posedge clk or posedge r)\n  if (r) q <= 0; else q <= d;",
    inputs: ["d", "r"],
    desc: "D Flip-Flop with async Reset. R overrides clock.",
    fn: null,
    category: "sequential",
  },
  dffsr_cell: {
    name: "DFF+SR",
    verilog: "always @(posedge clk or posedge s or posedge r)\n  if (r) q<=0; else if (s) q<=1; else q<=d;",
    inputs: ["d", "s", "r"],
    desc: "D Flip-Flop with async Set/Reset. R > S > D priority.",
    fn: null,
    category: "sequential",
  },
};

// Gate SVG symbols
function GateSymbol({ type, inputs, output, size = 120 }) {
  const w = size;
  const h = size * 0.7;
  const cx = w / 2;
  const cy = h / 2;

  const inColor = (v) => (v ? "#00ffa3" : "#334155");
  const outColor = (v) => (v ? "#00ffa3" : "#334155");
  const wireColor = "#475569";

  const inputVals = Object.values(inputs);
  const outputVal = output;

  const bodyStyle = {
    fill: "none",
    stroke: "#94a3b8",
    strokeWidth: 2,
  };

  const renderBody = () => {
    const gate = GATES[type];
    if (!gate) return null;

    switch (type) {
      case "buffer_cell":
        return (
          <g>
            <polygon
              points={`${cx - 20},${cy - 18} ${cx + 20},${cy} ${cx - 20},${cy + 18}`}
              {...bodyStyle}
            />
          </g>
        );
      case "not_cell":
        return (
          <g>
            <polygon
              points={`${cx - 20},${cy - 18} ${cx + 16},${cy} ${cx - 20},${cy + 18}`}
              {...bodyStyle}
            />
            <circle cx={cx + 21} cy={cy} r={4} {...bodyStyle} />
          </g>
        );
      case "and_cell":
        return (
          <path
            d={`M${cx - 18},${cy - 20} L${cx - 18},${cy + 20} L${cx},${cy + 20} A20,20 0 0,0 ${cx},${cy - 20} Z`}
            {...bodyStyle}
          />
        );
      case "nand_cell":
        return (
          <g>
            <path
              d={`M${cx - 18},${cy - 20} L${cx - 18},${cy + 20} L${cx},${cy + 20} A20,20 0 0,0 ${cx},${cy - 20} Z`}
              {...bodyStyle}
            />
            <circle cx={cx + 22} cy={cy} r={4} {...bodyStyle} />
          </g>
        );
      case "or_cell":
        return (
          <path
            d={`M${cx - 22},${cy - 20} Q${cx - 10},${cy} ${cx - 22},${cy + 20} Q${cx + 10},${cy + 20} ${cx + 20},${cy} Q${cx + 10},${cy - 20} ${cx - 22},${cy - 20}`}
            {...bodyStyle}
          />
        );
      case "nor_cell":
        return (
          <g>
            <path
              d={`M${cx - 22},${cy - 20} Q${cx - 10},${cy} ${cx - 22},${cy + 20} Q${cx + 10},${cy + 20} ${cx + 20},${cy} Q${cx + 10},${cy - 20} ${cx - 22},${cy - 20}`}
              {...bodyStyle}
            />
            <circle cx={cx + 24} cy={cy} r={4} {...bodyStyle} />
          </g>
        );
      case "xor_cell":
        return (
          <g>
            <path
              d={`M${cx - 22},${cy - 20} Q${cx - 10},${cy} ${cx - 22},${cy + 20} Q${cx + 10},${cy + 20} ${cx + 20},${cy} Q${cx + 10},${cy - 20} ${cx - 22},${cy - 20}`}
              {...bodyStyle}
            />
            <path
              d={`M${cx - 27},${cy - 20} Q${cx - 15},${cy} ${cx - 27},${cy + 20}`}
              fill="none"
              stroke="#94a3b8"
              strokeWidth={2}
            />
          </g>
        );
      case "xnor_cell":
        return (
          <g>
            <path
              d={`M${cx - 22},${cy - 20} Q${cx - 10},${cy} ${cx - 22},${cy + 20} Q${cx + 10},${cy + 20} ${cx + 20},${cy} Q${cx + 10},${cy - 20} ${cx - 22},${cy - 20}`}
              {...bodyStyle}
            />
            <path
              d={`M${cx - 27},${cy - 20} Q${cx - 15},${cy} ${cx - 27},${cy + 20}`}
              fill="none"
              stroke="#94a3b8"
              strokeWidth={2}
            />
            <circle cx={cx + 24} cy={cy} r={4} {...bodyStyle} />
          </g>
        );
      case "mux_cell":
        return (
          <polygon
            points={`${cx - 16},${cy - 24} ${cx + 16},${cy - 14} ${cx + 16},${cy + 14} ${cx - 16},${cy + 24}`}
            {...bodyStyle}
          />
        );
      case "dff_cell":
      case "dffr_cell":
      case "dffsr_cell":
        return (
          <g>
            <rect
              x={cx - 22}
              y={cy - 22}
              width={44}
              height={44}
              rx={3}
              {...bodyStyle}
            />
            <polyline
              points={`${cx - 22},${cy + 8} ${cx - 16},${cy + 14} ${cx - 22},${cy + 20}`}
              fill="none"
              stroke="#94a3b8"
              strokeWidth={1.5}
            />
            <text
              x={cx}
              y={cy - 6}
              textAnchor="middle"
              fill="#64748b"
              fontSize={9}
              fontFamily="monospace"
            >
              {type === "dff_cell" ? "DFF" : type === "dffr_cell" ? "DFF+R" : "DFF+SR"}
            </text>
          </g>
        );
      default:
        return (
          <rect
            x={cx - 20}
            y={cy - 20}
            width={40}
            height={40}
            rx={4}
            {...bodyStyle}
          />
        );
    }
  };

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      {renderBody()}

      {/* Input wires */}
      {GATES[type]?.category === "unary" && (
        <g>
          <line x1={8} y1={cy} x2={cx - 20} y2={cy} stroke={inColor(inputVals[0])} strokeWidth={2} />
          <circle cx={8} cy={cy} r={4} fill={inColor(inputVals[0])} />
        </g>
      )}
      {GATES[type]?.category === "binary" && (
        <g>
          <line x1={8} y1={cy - 10} x2={cx - 18} y2={cy - 10} stroke={inColor(inputVals[0])} strokeWidth={2} />
          <circle cx={8} cy={cy - 10} r={4} fill={inColor(inputVals[0])} />
          <line x1={8} y1={cy + 10} x2={cx - 18} y2={cy + 10} stroke={inColor(inputVals[1])} strokeWidth={2} />
          <circle cx={8} cy={cy + 10} r={4} fill={inColor(inputVals[1])} />
        </g>
      )}
      {GATES[type]?.category === "mux" && (
        <g>
          <line x1={8} y1={cy - 14} x2={cx - 16} y2={cy - 14} stroke={inColor(inputVals[0])} strokeWidth={2} />
          <circle cx={8} cy={cy - 14} r={4} fill={inColor(inputVals[0])} />
          <line x1={8} y1={cy + 2} x2={cx - 16} y2={cy + 2} stroke={inColor(inputVals[1])} strokeWidth={2} />
          <circle cx={8} cy={cy + 2} r={4} fill={inColor(inputVals[1])} />
          <line x1={cx} y1={h - 4} x2={cx} y2={cy + 14} stroke={inColor(inputVals[2])} strokeWidth={2} />
          <circle cx={cx} cy={h - 4} r={4} fill={inColor(inputVals[2])} />
        </g>
      )}

      {/* Output wire */}
      {GATES[type]?.category !== "sequential" && (
        <g>
          <line
            x1={type.includes("nor") || type === "xnor_cell" || type === "nand_cell" ? cx + 28 : type === "not_cell" ? cx + 25 : cx + 20}
            y1={cy}
            x2={w - 8}
            y2={cy}
            stroke={outColor(outputVal)}
            strokeWidth={2}
          />
          <circle cx={w - 8} cy={cy} r={4} fill={outColor(outputVal)} />
        </g>
      )}
    </svg>
  );
}

// Truth table generator
function TruthTable({ type }) {
  const gate = GATES[type];
  if (!gate || !gate.fn) return null;

  const inputs = gate.inputs;
  const rows = [];
  const combos = 1 << inputs.length;

  for (let i = 0; i < combos; i++) {
    const inputMap = {};
    inputs.forEach((name, idx) => {
      inputMap[name] = (i >> (inputs.length - 1 - idx)) & 1;
    });
    const result = gate.fn(inputMap);
    rows.push({ inputs: inputMap, output: result.out });
  }

  return (
    <div style={{ fontFamily: "'JetBrains Mono', 'Fira Code', monospace", fontSize: 11 }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            {inputs.map((name) => (
              <th
                key={name}
                style={{
                  padding: "4px 10px",
                  borderBottom: "1px solid #334155",
                  color: "#94a3b8",
                  textTransform: "uppercase",
                  fontSize: 10,
                  letterSpacing: 1,
                }}
              >
                {name}
              </th>
            ))}
            <th
              style={{
                padding: "4px 10px",
                borderBottom: "1px solid #334155",
                borderLeft: "1px solid #334155",
                color: "#00ffa3",
                fontSize: 10,
                letterSpacing: 1,
              }}
            >
              OUT
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {inputs.map((name) => (
                <td
                  key={name}
                  style={{
                    padding: "3px 10px",
                    textAlign: "center",
                    color: row.inputs[name] ? "#e2e8f0" : "#475569",
                    fontWeight: row.inputs[name] ? 700 : 400,
                  }}
                >
                  {row.inputs[name]}
                </td>
              ))}
              <td
                style={{
                  padding: "3px 10px",
                  textAlign: "center",
                  borderLeft: "1px solid #334155",
                  color: row.output ? "#00ffa3" : "#475569",
                  fontWeight: row.output ? 700 : 400,
                }}
              >
                {row.output}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Flip-flop waveform simulator
function FFSimulator({ type }) {
  const [history, setHistory] = useState([]);
  const [q, setQ] = useState(0);
  const [d, setD] = useState(0);
  const [r, setR] = useState(0);
  const [s, setS] = useState(0);
  const [clkState, setClkState] = useState(0);
  const maxSteps = 20;

  const clockTick = useCallback(() => {
    setClkState((prev) => {
      const newClk = prev ^ 1;
      if (newClk === 1) {
        // Rising edge
        setQ((prevQ) => {
          let newQ;
          if (type === "dff_cell") {
            newQ = d;
          } else if (type === "dffr_cell") {
            newQ = r ? 0 : d;
          } else {
            newQ = r ? 0 : s ? 1 : d;
          }
          setHistory((h) => {
            const entry = { clk: 1, d, r, s, q: newQ };
            return [...h.slice(-(maxSteps - 1)), entry];
          });
          return newQ;
        });
      } else {
        setHistory((h) => {
          const entry = { clk: 0, d, r, s, q };
          return [...h.slice(-(maxSteps - 1)), entry];
        });
      }
      return newClk;
    });
  }, [d, r, s, q, type]);

  // Async reset/set (immediate, no clock needed)
  useEffect(() => {
    if (r) {
      setQ(0);
    } else if (s && type === "dffsr_cell") {
      setQ(1);
    }
  }, [r, s, type]);

  const waveW = 440;
  const waveH = 120;
  const stepW = waveW / maxSteps;

  const renderWave = (data, key, yBase, color) => {
    if (data.length < 2) return null;
    let path = `M 0 ${yBase + (data[0][key] ? 0 : 16)}`;
    for (let i = 1; i < data.length; i++) {
      const x = i * stepW;
      const prevY = yBase + (data[i - 1][key] ? 0 : 16);
      const curY = yBase + (data[i][key] ? 0 : 16);
      if (prevY !== curY) path += ` L ${x} ${prevY} L ${x} ${curY}`;
      else path += ` L ${x} ${curY}`;
    }
    return <path d={path} fill="none" stroke={color} strokeWidth={1.5} />;
  };

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        <button
          onClick={clockTick}
          style={{
            background: clkState ? "#00ffa3" : "#1e293b",
            color: clkState ? "#0f172a" : "#94a3b8",
            border: "1px solid #334155",
            padding: "6px 16px",
            borderRadius: 4,
            cursor: "pointer",
            fontFamily: "monospace",
            fontWeight: 700,
            fontSize: 12,
          }}
        >
          CLK ⏎ ({clkState})
        </button>
        <button
          onClick={() => setD((v) => v ^ 1)}
          style={{
            background: d ? "#3b82f6" : "#1e293b",
            color: d ? "#fff" : "#94a3b8",
            border: "1px solid #334155",
            padding: "6px 16px",
            borderRadius: 4,
            cursor: "pointer",
            fontFamily: "monospace",
            fontSize: 12,
          }}
        >
          D = {d}
        </button>
        {(type === "dffr_cell" || type === "dffsr_cell") && (
          <button
            onClick={() => setR((v) => v ^ 1)}
            style={{
              background: r ? "#ef4444" : "#1e293b",
              color: r ? "#fff" : "#94a3b8",
              border: "1px solid #334155",
              padding: "6px 16px",
              borderRadius: 4,
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 12,
            }}
          >
            R = {r}
          </button>
        )}
        {type === "dffsr_cell" && (
          <button
            onClick={() => setS((v) => v ^ 1)}
            style={{
              background: s ? "#f59e0b" : "#1e293b",
              color: s ? "#000" : "#94a3b8",
              border: "1px solid #334155",
              padding: "6px 16px",
              borderRadius: 4,
              cursor: "pointer",
              fontFamily: "monospace",
              fontSize: 12,
            }}
          >
            S = {s}
          </button>
        )}
        <div
          style={{
            marginLeft: "auto",
            padding: "6px 16px",
            background: q ? "#00ffa320" : "#1e293b",
            border: `1px solid ${q ? "#00ffa3" : "#334155"}`,
            borderRadius: 4,
            fontFamily: "monospace",
            color: q ? "#00ffa3" : "#475569",
            fontWeight: 700,
            fontSize: 12,
          }}
        >
          Q = {q}
        </div>
      </div>

      {history.length > 1 && (
        <svg
          width="100%"
          viewBox={`0 0 ${waveW} ${waveH}`}
          style={{ background: "#0c1222", borderRadius: 6, border: "1px solid #1e293b" }}
        >
          {/* Labels */}
          <text x={waveW - 4} y={12} fill="#94a3b8" fontSize={8} textAnchor="end" fontFamily="monospace">CLK</text>
          <text x={waveW - 4} y={36} fill="#3b82f6" fontSize={8} textAnchor="end" fontFamily="monospace">D</text>
          <text x={waveW - 4} y={60} fill="#00ffa3" fontSize={8} textAnchor="end" fontFamily="monospace">Q</text>
          {(type === "dffr_cell" || type === "dffsr_cell") && (
            <text x={waveW - 4} y={84} fill="#ef4444" fontSize={8} textAnchor="end" fontFamily="monospace">R</text>
          )}
          {type === "dffsr_cell" && (
            <text x={waveW - 4} y={108} fill="#f59e0b" fontSize={8} textAnchor="end" fontFamily="monospace">S</text>
          )}

          {renderWave(history, "clk", 4, "#94a3b8")}
          {renderWave(history, "d", 28, "#3b82f6")}
          {renderWave(history, "q", 52, "#00ffa3")}
          {(type === "dffr_cell" || type === "dffsr_cell") && renderWave(history, "r", 76, "#ef4444")}
          {type === "dffsr_cell" && renderWave(history, "s", 100, "#f59e0b")}
        </svg>
      )}
      {history.length <= 1 && (
        <div
          style={{
            height: 80,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#334155",
            fontFamily: "monospace",
            fontSize: 11,
            background: "#0c1222",
            borderRadius: 6,
            border: "1px solid #1e293b",
          }}
        >
          Click CLK to generate waveform →
        </div>
      )}
    </div>
  );
}

// Interactive gate card
function GateCard({ type, gate }) {
  const [inputs, setInputs] = useState(() => {
    const init = {};
    gate.inputs.forEach((name) => (init[name] = 0));
    return init;
  });

  const toggleInput = (name) => {
    setInputs((prev) => ({ ...prev, [name]: prev[name] ^ 1 }));
  };

  const output = gate.fn ? gate.fn(inputs).out : null;
  const isSeq = gate.category === "sequential";

  return (
    <div
      style={{
        background: "#0f172a",
        border: "1px solid #1e293b",
        borderRadius: 8,
        padding: 20,
        display: "flex",
        flexDirection: "column",
        gap: 12,
        transition: "border-color 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#00ffa340")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1e293b")}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <span
            style={{
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              fontSize: 18,
              fontWeight: 800,
              color: "#e2e8f0",
              letterSpacing: 1,
            }}
          >
            {gate.name}
          </span>
          <span
            style={{
              marginLeft: 8,
              fontSize: 10,
              color: "#475569",
              fontFamily: "monospace",
              letterSpacing: 0.5,
            }}
          >
            {type}
          </span>
        </div>
        <span
          style={{
            fontSize: 9,
            padding: "2px 8px",
            borderRadius: 3,
            background: isSeq ? "#1e1b4b" : "#0c2a1f",
            color: isSeq ? "#818cf8" : "#00ffa3",
            fontFamily: "monospace",
            textTransform: "uppercase",
            letterSpacing: 1,
          }}
        >
          {isSeq ? "sequential" : "combinational"}
        </span>
      </div>

      {/* Description */}
      <p style={{ margin: 0, fontSize: 12, color: "#64748b", lineHeight: 1.5 }}>{gate.desc}</p>

      {/* Verilog */}
      <div
        style={{
          background: "#0c1222",
          borderRadius: 4,
          padding: "8px 12px",
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          fontSize: 11,
          color: "#7dd3fc",
          whiteSpace: "pre-wrap",
          borderLeft: "2px solid #0ea5e9",
        }}
      >
        {gate.verilog}
      </div>

      {!isSeq ? (
        <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
          {/* Symbol + interactive inputs */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <GateSymbol type={type} inputs={inputs} output={output} size={120} />
            <div style={{ display: "flex", gap: 6 }}>
              {gate.inputs.map((name) => (
                <button
                  key={name}
                  onClick={() => toggleInput(name)}
                  style={{
                    width: 40,
                    height: 28,
                    borderRadius: 4,
                    border: `1px solid ${inputs[name] ? "#00ffa3" : "#334155"}`,
                    background: inputs[name] ? "#00ffa320" : "#1e293b",
                    color: inputs[name] ? "#00ffa3" : "#475569",
                    fontFamily: "monospace",
                    fontWeight: 700,
                    fontSize: 11,
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {name}={inputs[name]}
                </button>
              ))}
            </div>
            <div
              style={{
                fontSize: 13,
                fontFamily: "monospace",
                fontWeight: 800,
                color: output ? "#00ffa3" : "#334155",
                transition: "color 0.15s",
              }}
            >
              out = {output}
            </div>
          </div>

          {/* Truth table */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <TruthTable type={type} />
          </div>
        </div>
      ) : (
        <FFSimulator type={type} />
      )}
    </div>
  );
}

// Main app
export default function CitadelPrimitives() {
  const [filter, setFilter] = useState("all");
  const categories = [
    { key: "all", label: "ALL" },
    { key: "combinational", label: "COMB" },
    { key: "sequential", label: "SEQ" },
  ];

  const filtered = Object.entries(GATES).filter(([, g]) => {
    if (filter === "all") return true;
    if (filter === "combinational") return g.category !== "sequential";
    return g.category === "sequential";
  });

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#080e1a",
        color: "#e2e8f0",
        fontFamily:
          "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          borderBottom: "1px solid #1e293b",
          padding: "24px 32px",
          background: "linear-gradient(180deg, #0f172a 0%, #080e1a 100%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
          <h1
            style={{
              margin: 0,
              fontSize: 22,
              fontWeight: 800,
              letterSpacing: 2,
              color: "#00ffa3",
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            }}
          >
            CITADEL PRIMITIVES
          </h1>
          <span style={{ fontSize: 12, color: "#475569", fontFamily: "monospace" }}>
            cells.v — Gate Atlas v1.0
          </span>
        </div>
        <p style={{ margin: "8px 0 0", fontSize: 13, color: "#64748b", maxWidth: 600 }}>
          Interactive visualization of the 12 structural Verilog cells that form the foundation of
          the Sentinel Lock. Toggle inputs, explore truth tables, and simulate flip-flop timing.
        </p>

        {/* Filter bar */}
        <div style={{ display: "flex", gap: 6, marginTop: 16 }}>
          {categories.map((c) => (
            <button
              key={c.key}
              onClick={() => setFilter(c.key)}
              style={{
                padding: "5px 16px",
                borderRadius: 4,
                border: `1px solid ${filter === c.key ? "#00ffa3" : "#334155"}`,
                background: filter === c.key ? "#00ffa320" : "transparent",
                color: filter === c.key ? "#00ffa3" : "#64748b",
                fontFamily: "monospace",
                fontSize: 11,
                fontWeight: 700,
                cursor: "pointer",
                letterSpacing: 1,
                transition: "all 0.15s",
              }}
            >
              {c.label}
              <span style={{ marginLeft: 6, opacity: 0.5 }}>
                (
                {c.key === "all"
                  ? Object.keys(GATES).length
                  : Object.values(GATES).filter((g) =>
                      c.key === "combinational"
                        ? g.category !== "sequential"
                        : g.category === "sequential"
                    ).length}
                )
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div
        style={{
          padding: "24px 32px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(420px, 1fr))",
          gap: 16,
        }}
      >
        {filtered.map(([key, gate]) => (
          <GateCard key={key} type={key} gate={gate} />
        ))}
      </div>

      {/* Footer */}
      <div
        style={{
          borderTop: "1px solid #1e293b",
          padding: "16px 32px",
          textAlign: "center",
          fontFamily: "monospace",
          fontSize: 10,
          color: "#334155",
          letterSpacing: 1,
        }}
      >
        VAELIX SYSTEMS — PROJECT CITADEL — (* keep_hierarchy *) ENFORCED — 12 PRIMITIVES / IHP 130nm SG13G2
      </div>
    </div>
  );
}
