End-to-End Packaging Flow

Duration: 2 weeks
Goal: Ship a fully working “upload → metadata → AI → render → download/copy” flow, keep the codebase lean (KISS).

Tickets
🧹 Knowledge Base Cleanup (Phase 0)
ID	Task
SP6-00	✅ Remove ChromaDB/RAG dependencies: Delete knowledge_base.py, switches.yaml, chroma_db/ directory, clean up all related imports/calls, and remove chromadb from requirements.

🗂️ Repository & Tooling
ID	Task
SP6-01	Create /uploads/ folder inside instance/ and add it to .gitignore.
SP6-02	Add secure_filename helper & unit test for path safety.

📂 File Handling
ID	Task
SP6-03	Save uploaded installer. In create_package_from_form, persist the file to instance/uploads/{package_uuid}_{filename} and update Package.installer_path.
SP6-04	Add basic error handling if disk write fails; bubble an error to the UI.

🏷️ Metadata Extraction
ID	Task
SP6-05	Create module metadata/extract.py with extract_metadata(path: Path) -> InstallerMetadata.
SP6-06	MSI: call lessmsi info <file> via subprocess; parse ProductName, ProductVersion, architecture (32/64).
SP6-07	EXE: detect installer type with lightweight header check → use hardcoded default silent switches (no YAML lookup).
SP6-08	Unit tests: feed sample MSI/EXE stubs, assert correct metadata objects.

🧠 AI Script Generation & Rendering
ID	Task
SP6-09	Replace placeholder metadata with real InstallerMetadata from SP6-05 in generate_and_update_package.
SP6-10	Wire ScriptRenderer.render_psadt_script() right after successful function-call parse; store rendered script in DB.
SP6-11	Adjust ComplianceLinter to validate the rendered output.

🔄 Job Resumption
ID	Task
SP6-12	Implement resume_incomplete_jobs() to relaunch IN_PROGRESS / PENDING packages on app start.
SP6-13	Mark un-resumable jobs as FAILED with a friendly message.

💻 UI Enhancements
ID	Task
SP6-14	Add “Copy Script” button on history page; use navigator.clipboard.writeText.
SP6-15	Surface FAILED/COMPLETED status badges in history list.

🧪 Tests
ID	Task
SP6-16	Happy-path integration test: upload MSI → wait → assert 200 download & correct header/version in script.
SP6-17	Resume test: mark package IN_PROGRESS, restart app, assert job completes.

📃 Docs
ID	Task
SP6-18	Update project_plan.md with new flow diagram and installation notes for LessMSI.
SP6-19	Add short HOW-TO in README: “Upload → Progress → Download/Copy”.
