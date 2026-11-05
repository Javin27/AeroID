import { Video, ScanFace, Image, Radio } from 'lucide-react'
// Placeholder panels for the future drone-camera integration.
// Replace the feed <div> with a <video>/<img> stream and set `detection` from your detector.
export default function LiveDetection() {
  const detection = { status: 'Waiting for camera', face: null }
  return (
    <div className="live">
      <div className="card feed">
        <span className="badge"><Radio size={14} /> Not connected</span>
        <Video size={44} /><h3>Drone camera feed</h3><p>The live stream will appear here once the drone is linked.</p>
        <i className="corner tl" /><i className="corner tr" /><i className="corner bl" /><i className="corner br" />
      </div>
      <div className="card side">
        <h3 className="h">Detection status</h3>
        <p className="pill">{detection.status}</p>
        <h3 className="h">Latest captured image</h3>
        <div className="ph"><Image size={28} /><span>No capture yet</span></div>
        <h3 className="h">Detected face</h3>
        <div className="ph face"><ScanFace size={28} /><span>{detection.face ?? 'No face detected'}</span></div>
      </div>
    </div>
  )
}
