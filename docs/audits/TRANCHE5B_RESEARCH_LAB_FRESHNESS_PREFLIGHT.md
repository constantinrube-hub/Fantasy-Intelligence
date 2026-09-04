# Tranche 5B Preflight — Research/Lab Navigation and Freshness

## Purpose

This characterization-only package freezes the current Research/Lab navigation and freshness behavior before any interface change. It changes no projection, rank, recommendation, evidence availability, or promotion decision.

## Current navigation

Lab exposes nine sibling tabs: Validation, M1 Research, M2 Research, M3 Research, M4 Research, M5 Decisions, M6 Production, Features, and Model & Data. All six milestone panels are separate routed surfaces. The League Research Report is additionally exposed through its own floating Research/Lab launcher and overlay rather than through the Lab navigation.

## Current freshness presentation

The underlying evidence layer already carries typed `asOf` metadata, and governance performs a real maximum-age check. Presentation is fragmented: the M5 badge shows only season/week, M6 exposes freshness through governance state, Runtime & Data Quality shows a raw build timestamp, and weekly status uses separate prose.

## Target boundary

The later target may group Lab entry points and add one display-only freshness presenter. It must preserve every legacy milestone route, keep the report evidence-only, and must never reinterpret stale or unavailable evidence as current.

## Preflight success condition

The dedicated workflow must reproduce the known-gap marker, preserve the completed semantic UX and earlier runtime/research contracts, pass the 22-league/six-format matrix, and produce `DEPLOYABLE_SOURCE` without generated drift.
