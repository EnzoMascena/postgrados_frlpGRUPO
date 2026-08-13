import { IconUpload } from '@tabler/icons-react'

type Props = {
  label: string
  optional?: boolean
  hint?: string
}

export default function UploadBox({ label, optional, hint = 'máx 5 MB' }: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[13px] text-muted">
        {label} {optional && <span className="text-faint">(opcional)</span>}
      </span>
      <label className="border border-dashed border-line-strong rounded-input p-3 text-center cursor-pointer bg-surface hover:border-primary transition-colors">
        <input type="file" accept="application/pdf" className="hidden" />
        <IconUpload size={20} stroke={1.5} className="mx-auto mb-1 text-faint" />
        <span className="block text-[13px] text-muted">Seleccionar archivo PDF</span>
        <span className="block text-[11px] text-faint mt-0.5">{hint}</span>
      </label>
    </div>
  )
}