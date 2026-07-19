---
title: "Statistics: Shuffling Cards & Markov Chains"
date: 2026-05-19
draft: false
slug: "markov-chains"
---
This project, which was my Master's dissertation, explored how Markov chains can explain the mathematics of shuffling, and how long it takes a deck to truly be shuffled.
<!--more-->
This project uses the theory of finite Markov chains to answer a deceptively simple question, how many times do you need to shuffle a deck of cards before we can really say it's 'shuffled'?

The paper builds up from the most basic principles; Markov chains, stationary distributions, and total variation distance (a way of measuring how "close to random" a deck actually is), before applying these tools to real shuffling methods. The paper mainly explores the riffle shuffle, but also touches on others such as top-to-random and wash shuffling.

The central result is a proof that **13 riffle shuffles are sufficient** to guarantee the mixing a standard 52-card deck, but almost always less shuffles will be needed. I then explore lower bounds via Wilson's method and eigenvalue analysis, and examine the  **cut-off phenomenon**, the surprising fact that a deck doesn't gradually become random, instead transitioning from non-random to shuffled within a narrow window of just a few shuffles, somewhere around 5-8 shuffles.

The final section moves beyond riffle shuffling to model the aforementioned **wash shuffling** (spreading cards on a table by hand) as a spatial mixing process, including a computer simulation I built to test how quickly this method randomizes a deck in practice, finding that roughly 30 seconds of wash shuffling is enough to reach a well-mixed state.

## Downloads

<a href="/files/markovchains-mguinness.pdf" download>📄 Download my full dissertation (.pdf)</a>
