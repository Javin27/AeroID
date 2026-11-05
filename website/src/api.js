const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

// Look up one student. Returns { ok, status, data } or { ok:false, status:'offline' }.
export async function fetchStudent(admission) {
  try {
    const res = await fetch(`${BASE}/api/students/${encodeURIComponent(admission)}`)
    if (res.status === 404) return { ok: false, status: 404 }
    if (!res.ok) return { ok: false, status: res.status }
    return { ok: true, data: await res.json() }
  } catch {
    return { ok: false, status: 'offline' }
  }
}

// Backend health + total students. Any HTTP response means the server is reachable.
export async function fetchSystem() {
  try {
    const res = await fetch(`${BASE}/api/students`)
    let total = null
    if (res.ok) {
      const j = await res.json()
      total = Array.isArray(j) ? j.length
        : Array.isArray(j.students) ? j.students.length
        : j.total ?? j.count ?? null
    }
    return { online: true, total }
  } catch {
    return { online: false, total: null }
  }
}

// The backend's field names may vary; read the first one present.
const KEYS = {
  name: ['name', 'student_name', 'full_name'],
  admission: ['admission_number', 'admission_no', 'admission'],
  class: ['class', 'class_name', 'grade'],
  section: ['section'],
  roll: ['roll_number', 'roll_no', 'roll'],
  dob: ['date_of_birth', 'dob'],
  parent: ['parent_name', 'parent', 'guardian_name'],
  contact: ['contact_number', 'contact', 'phone', 'parent_contact'],
  address: ['address']
}
export function pick(obj, field) {
  const src = obj?.student ?? obj
  for (const k of KEYS[field]) if (src?.[k] != null && src[k] !== '') return String(src[k])
  return '—'
}

// Send a face image to the backend (InsightFace buffalo_l). Expected 200 reply:
// { match: true, admission_number: "1234", confidence: 0.82, bbox: [x1,y1,x2,y2] }
// 404 / 422 with { error } means no match / no face found.
export async function recognizeFace(blob) {
  try {
    const fd = new FormData()
    fd.append('image', blob, 'capture.jpg')
    const res = await fetch(`${BASE}/api/recognize`, { method: 'POST', body: fd })
    const j = await res.json().catch(() => ({}))
    if (!res.ok || j.match === false) return { ok: false, status: res.status, message: j.error || j.message }
    return { ok: true, data: j }
  } catch {
    return { ok: false, status: 'offline' }
  }
}
