import { useState, type FC } from "react";
import {
  approveGmailDraft,
  cancelGmailDraftApproval,
  type GmailApprovalDto,
} from "@/lib/backendAssistantClient";

type GmailApprovalCardProps = {
  approval: GmailApprovalDto;
  onChange: (approval: GmailApprovalDto) => void;
};

const statusLabels: Record<GmailApprovalDto["status"], string> = {
  pending: "Pending approval",
  approved: "Approved",
  cancelled: "Cancelled",
  expired: "Expired",
  invalidated: "Draft changed - approval invalidated",
};

function formatSize(sizeBytes?: number): string | null {
  if (typeof sizeBytes !== "number" || sizeBytes < 0) return null;
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function recipients(values: string[]): string {
  return values.length > 0 ? values.join(", ") : "None";
}

export const GmailApprovalCard: FC<GmailApprovalCardProps> = ({ approval, onChange }) => {
  const [loading, setLoading] = useState<"approve" | "cancel" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isPending = approval.status === "pending";

  const changeApproval = async (action: "approve" | "cancel") => {
    if (!isPending || loading) return;
    setLoading(action);
    setErrorMessage(null);
    try {
      const response = action === "approve"
        ? await approveGmailDraft(approval.approval_id)
        : await cancelGmailDraftApproval(approval.approval_id);
      if (!response.approval) {
        throw new Error(response.error || "Approval could not be updated.");
      }
      const updatedApproval = Object.fromEntries(
        Object.entries(response.approval).filter(([, value]) => value !== undefined),
      ) as Partial<GmailApprovalDto>;
      onChange({ ...approval, ...updatedApproval });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Approval could not be updated.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <section className="gmail-approval-card" aria-label="Gmail draft approval">
      <header className="gmail-approval-header">
        <div>
          <p className="eyebrow">Gmail Draft Approval</p>
          <h3>Review before approval</h3>
        </div>
        <span className={`gmail-approval-status ${approval.status}`}>
          {statusLabels[approval.status]}
        </span>
      </header>

      <div className="gmail-approval-details">
        <div><span>Account</span><strong>{approval.active_account_id}</strong></div>
        <div><span>To</span><strong>{recipients(approval.to)}</strong></div>
        <div><span>CC</span><strong>{recipients(approval.cc)}</strong></div>
        <div><span>BCC</span><strong>{recipients(approval.bcc)}</strong></div>
        <div><span>Subject</span><strong>{approval.subject || "(No subject)"}</strong></div>
      </div>

      <div className="gmail-approval-body">
        <span>Body</span>
        <p>{approval.body || "Body preview is unavailable."}</p>
      </div>

      <div className="gmail-approval-attachments">
        <span>Attachments</span>
        {approval.attachment_metadata.length === 0 ? (
          <p>None</p>
        ) : (
          <ul>
            {approval.attachment_metadata.map((attachment, index) => {
              const size = formatSize(attachment.size_bytes);
              return (
                <li key={`${attachment.file_name}-${index}`}>
                  <strong>{attachment.file_name}</strong>
                  {attachment.mime_type ? ` - ${attachment.mime_type}` : ""}
                  {size ? ` - ${size}` : ""}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="gmail-approval-expiry">
        Expires {new Date(approval.expires_at).toLocaleString()}
      </div>

      {isPending && (
        <div className="gmail-approval-actions">
          <button
            type="button"
            className="gmail-approval-approve"
            onClick={() => void changeApproval("approve")}
            disabled={loading !== null}
          >
            {loading === "approve" ? "Approving..." : "Approve Draft"}
          </button>
          <button
            type="button"
            className="gmail-approval-cancel"
            onClick={() => void changeApproval("cancel")}
            disabled={loading !== null}
          >
            {loading === "cancel" ? "Cancelling..." : "Cancel"}
          </button>
        </div>
      )}

      {approval.status === "approved" && (
        <p className="gmail-approval-note">Sending is not enabled in this phase.</p>
      )}
      {errorMessage && <p className="gmail-approval-error">{errorMessage}</p>}
    </section>
  );
};
