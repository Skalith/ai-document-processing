// Dotted-path helpers for the Human Verification / Edit layer.
//
// Work on plain (JSON-safe) structured_data objects. Flatten nested schema
// dicts to dotted leaf paths such as "line_items[0].amount", diff the AI
// original against the user-edited copy, and build a tracked changes[]
// list. Never mutates inputs — every helper returns fresh copies.

// Split a dotted path with array brackets into plain segments, turning
// "line_items[2].quantity" into ["line_items", "2", "quantity"].
function pathSegments(dottedPath) {
  return dottedPath
    .split(/(\[[0-9]+\])|\./)
    .filter(Boolean)
    .map((seg) => {
      const arrMatch = /^\[([0-9]+)\]$/.exec(seg);
      return arrMatch ? arrMatch[1] : seg;
    });
}

function deepClone(value) {
  if (value === null || value === undefined) return value;
  if (Array.isArray(value)) return value.map(deepClone);
  if (typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value)) out[key] = deepClone(value[key]);
    return out;
  }
  return value;
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((item, i) => deepEqual(item, b[i]));
  }
  if (a && b && typeof a === "object" && typeof b === "object") {
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    return ka.every((key) => key in b && deepEqual(a[key], b[key]));
  }
  return false;
}

// Deep-clone `data` and set the scalar/leaf/collection at `dottedPath`.
export function applyEdit(data, dottedPath, value) {
  const copy = deepClone(data ?? {});
  const segments = pathSegments(dottedPath);
  let current = copy;

  for (let i = 0; i < segments.length - 1; i += 1) {
    const seg = segments[i];
    if (Array.isArray(current)) {
      current = current[Number(seg)];
    } else {
      const next = current[seg];
      if (next === undefined || next === null) current[seg] = {};
      current = current[seg];
    }
    if (current === undefined) break;
  }

  const last = segments[segments.length - 1];
  if (Array.isArray(current)) {
    current[Number(last)] = value;
  } else if (current && typeof current === "object") {
    current[last] = value;
  }
  return copy;
}

// Recursively compare the AI original with the user copy, returning the
// tracked changes[{field, aiValue, userValue, kind, type, changedAt, status}].
export function diffChanges(aiValue, userValue) {
  const changes = [];

  const walk = (aiNode, userNode, path) => {
    const aIsArr = Array.isArray(aiNode);
    const uIsArr = Array.isArray(userNode);

    if (aIsArr || uIsArr) {
      const aArr = aIsArr ? aiNode : [];
      const uArr = uIsArr ? userNode : null;

      if (aArr.length === uArr?.length) {
        // Same-size arrays: diff element-by-element so edits land on
        // granular dotted leaves like line_items[0].amount.
        aArr.forEach((item, i) => walk(item, uArr?.[i], `${path}[${i}]`));
        return;
      }

      // Length changed (row added/removed): report the collection as one
      // change so the diff stays terse and meaningful.
      if (!deepEqual(aArr, uArr)) {
        changes.push({
          field: path,
          aiValue: deepClone(aiNode),
          userValue: deepClone(userNode),
          kind: "collection",
          type: "string",
          changedAt: new Date().toISOString(),
          status: "edited",
        });
      }
      return;
    }

    if (aiNode && userNode && typeof aiNode === "object" && typeof userNode === "object") {
      const keys = new Set([...Object.keys(aiNode), ...Object.keys(userNode)]);
      for (const key of keys) {
        walk(aiNode[key], userNode[key], path ? `${path}.${key}` : key);
      }
      return;
    }

    if (!deepEqual(aiNode, userNode)) {
      const probe = userNode ?? aiNode;
      changes.push({
        field: path,
        aiValue: deepClone(aiNode),
        userValue: deepClone(userNode),
        kind: "leaf",
        type: typeof probe === "number" ? "number" : "string",
        changedAt: new Date().toISOString(),
        status: "edited",
      });
    }
  };

  walk(aiValue, userValue, "");
  return changes;
}

// Fresh user_result wrapper: a deep copy of the AI data plus an empty
// changes[] list (nothing edited yet).
export function emptyUserResult(aiValue) {
  return { structured_data: deepClone(aiValue ?? null), changes: [] };
}

// Recompute the changes[] list from the AI original and edited data copy.
export function rebuildUserResult(aiValue, editedData) {
  return {
    structured_data: deepClone(editedData ?? null),
    changes: diffChanges(aiValue ?? null, editedData ?? null),
  };
}

// Dotted-path list of every scalar leaf in a nested object/array.
export function leafPaths(value, prefix = "") {
  const out = [];
  const walk = (node, path) => {
    if (Array.isArray(node)) {
      node.forEach((item, i) => walk(item, `${path}[${i}]`));
    } else if (node && typeof node === "object") {
      for (const key of Object.keys(node)) {
        walk(node[key], path ? `${path}.${key}` : key);
      }
    } else {
      out.push(path);
    }
  };
  walk(value, prefix);
  return out.sort();
}

export function isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

export { deepClone };