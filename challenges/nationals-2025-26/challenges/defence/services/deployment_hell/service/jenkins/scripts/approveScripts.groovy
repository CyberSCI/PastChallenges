
import org.jenkinsci.plugins.scriptsecurity.scripts.ScriptApproval

def approval = ScriptApproval.get()
approval.pendingSignatures.each { sig ->
    approval.approveSignature(sig.signature)
    println "Approved: ${sig.signature}"
}
