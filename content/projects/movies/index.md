---
title: "Visualisation: Movie Map"
date: 2026-07-27
draft: false
slug: "movie-map"
---
A 2-D interactive map of 40,000 films and documentaries, grouped by similarity using 626 dimensional vectors, UMAP and HDBSCAN.
<!--more-->

## View the Project

<a href="https://mikeyguinness.com/movies" target="_blank" rel="noopener">🎬 View the map here -></a>

## How it was built

The pipeline has four stages, three small python scripts feeding each other, and one html file.

## Fetching the data.

The first script pulls the top ~40,000 films by popularity from the TMDB API, using their daily ID export to know which films exist, then fetching full metadata for each. This includes genres, keywords, cast, crew, runtime, ratings, language, and more. Everything is cached into a local SQLite database, with throttling and fail safes so the fetch can be stopped and restarted without losing progress or hammering the API.

## Building the vectors.

The second stage turns each film's metadata into a single numeric vector. Genres and the most common keywords and people become multi-hot encodings, while numeric fields like runtime, year, and popularity are log-scaled and standardised. Each block is weighted so that semantic content (genre and theme) drives similarity more than raw numbers. The result is every film represented as a point in roughly 600-dimensional space.

## Reducing and clustering.

Six hundred dimensions can't be drawn, so the third stage does two independent jobs. It uses PCA and UMAP to project the vectors down to two-dimensional map coordinates that preserve which films are near which. Separately, it runs HDBSCAN clustering on the full-detail vectors to assign each film to a group, clustering on the rich representation rather than the flattened map, so the groups reflect genuine similarity. It also precomputes each film's twenty nearest neighbours for the "similar films" feature, and assigns colours to clusters and the films in them, while in-between films blend the colours of the nearest cluster edges, giving the map a continuous, flowing feel.

## HTML.

The frontend is a single HTML file rendering everything on an HTML5 Canvas, chosen because drawing tens of thousands of individual page elements would overwhelm a browser, whereas a canvas handles them as pixels with ease. It loads one JSON file of points and runs with no server, no build step, and no dependencies.

<sub>This product uses the TMDB API but is not endorsed or certified by TMDB.</sub>
