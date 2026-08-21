import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(
        ROOT
        / "packages"
        / "instrument_qualification"
        / "src"
    ),
)


from instrument_qualification import (
    CheckDefinition,
    CheckStatus,
    QualificationCatalog,
    QualificationReport,
    QualificationSession,
    QualificationSkip,
    generate_report_markdown,
    save_report_json,
)


def main():

    session = QualificationSession()

    session.run(
        CheckDefinition(
            id="identity",
            name="Identity",
            category="identity",
            mandatory=True,
        ),
        lambda: {
            "model": "DSO-X 3034A",
            "firmware": "02.50",
        },
    )

    session.run(
        CheckDefinition(
            id="waveform",
            name="Waveform",
            category="waveform",
            mandatory=True,
        ),
        lambda: {
            "points": 10000
        },
    )

    session.run(
        CheckDefinition(
            id="optional",
            name="Optional Measurement",
            category="measurement",
            mandatory=False,
        ),
        lambda: (_ for _ in ()).throw(
            QualificationSkip(
                "No input signal"
            )
        ),
    )

    session.finish()

    report = QualificationReport(
        driver_family="DSOX3000",
        target_model="DSO-X 3034A",
        driver_version="0.1.0",
        firmware="02.50",
        serial_number="MY123456",
        resource="MOCK",
        instrument_identity={
            "manufacturer": (
                "KEYSIGHT TECHNOLOGIES"
            ),
            "model": "DSO-X 3034A",
        },
        checks=session.results,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )

    assert report.passed() == 2
    assert report.failed() == 0
    assert report.skipped() == 1

    assert (
        report.eligible_for_qualified()
        is True
    )

    assert (
        session.results[2].status
        == CheckStatus.SKIPPED
    )

    failed_session = (
        QualificationSession()
    )

    failed_session.run(
        CheckDefinition(
            id="mandatory",
            name="Mandatory",
            category="test",
            mandatory=True,
        ),
        lambda: False,
    )

    failed_report = QualificationReport(
        driver_family="TEST",
        target_model="TEST",
        instrument_identity={},
        checks=failed_session.results,
    )

    assert (
        failed_report.eligible_for_qualified()
        is False
    )

    dsox_catalog = (
        QualificationCatalog.load_json(
            ROOT
            / "instrument_profiles"
            / "keysight"
            / "dsox3000"
            / "qualification"
            / "requirements.json"
        )
    )

    fsw_catalog = (
        QualificationCatalog.load_json(
            ROOT
            / "instrument_profiles"
            / "rohde_schwarz"
            / "fsw"
            / "qualification"
            / "requirements.json"
        )
    )

    assert len(
        dsox_catalog.checks
    ) >= 10

    assert len(
        fsw_catalog.checks
    ) >= 10

    with tempfile.TemporaryDirectory() as temp:

        json_path = (
            Path(temp)
            / "report.json"
        )

        md_path = (
            Path(temp)
            / "report.md"
        )

        save_report_json(
            json_path,
            report,
        )

        generate_report_markdown(
            md_path,
            report,
        )

        payload = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            payload["summary"]
            ["eligible_for_qualified"]
            is True
        )

        assert md_path.exists()

    print(
        "Qualification framework self-test PASS"
    )

    print(
        "DSOX3000 requirements:",
        len(dsox_catalog.checks),
    )

    print(
        "FSW requirements:",
        len(fsw_catalog.checks),
    )


if __name__ == "__main__":
    main()
