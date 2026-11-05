import { User, Hash, School, Layers, ListOrdered, Cake, Users, Phone, MapPin } from 'lucide-react'
import { pick } from '../api'
const fields = [
  ['admission', 'Admission number', Hash], ['class', 'Class', School], ['section', 'Section', Layers],
  ['roll', 'Roll number', ListOrdered], ['dob', 'Date of birth', Cake], ['parent', 'Parent name', Users],
  ['contact', 'Contact number', Phone], ['address', 'Address', MapPin]
]
export default function StudentCard({ data }) {
  const name = pick(data, 'name')
  return (
    <article className="card student">
      <header>
        <div className="avatar"><User size={28} /></div>
        <div><small>Student name</small><h2>{name}</h2></div>
      </header>
      <dl>
        {fields.map(([k, label, Icon]) => (
          <div key={k} className={k === 'address' ? 'wide' : ''}>
            <dt><Icon size={14} />{label}</dt><dd>{pick(data, k)}</dd>
          </div>
        ))}
      </dl>
    </article>
  )
}
