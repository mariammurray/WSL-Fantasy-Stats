<script setup>
import { computed, onMounted, ref } from 'vue'
import { clubColorCode } from './data/clubColours'

const players = ref([])
const loading = ref(true)
const error = ref('')
const activeView = ref('all')
const weeklyPointsByPlayer = ref(new Map())
const snapshotBatches = ref(new Map())
const selectedMatchday = ref(2)

const leagueNames = {
  'wpll::Football_Competition::e32284e8a1214f1ca83a3245d690b336': 'WSL',
  'wpll::Football_Competition::422757a2c70d450eba118ad97bed5222': 'WSL 2',
}

const mediaBaseUrl = 'https://media-sdp.wslfootball.com/'
const localAssetUrl = (path) => `${import.meta.env.BASE_URL}${path}`

const mediaUrl = (path) => path ? `${mediaBaseUrl}${path}` : ''

const playerImageUrls = (player) => [
  player.teamImagery?.playerImage_home_celeb,
  player.teamImagery?.playerImage_home_left,
  player.teamImagery?.playerImage_home_right,
].filter(Boolean).map(mediaUrl)

const handlePlayerImageError = (event, player) => {
  event.target.classList.add('is-fallback')
  const currentIndex = Number(event.target.dataset.imageIndex ?? 0)
  const nextUrl = player.imageUrls[currentIndex + 1]

  if (nextUrl) {
    event.target.dataset.imageIndex = currentIndex + 1
    event.target.src = nextUrl
    return
  }

  event.target.src = localAssetUrl('user-solid-full.svg')
  event.target.alt = 'Default player profile icon'
}

const teamLogoUrl = (player) => mediaUrl(
  player.teamImagery?.teamLogo
  ?? `clubLogos/${player.teamId.replace('wpll::Football_Team::', '')}.webp`,
)

const snapshots = [
  localAssetUrl('data/matchday_1.json'),
  localAssetUrl('data/matchday_2.json'),
]

const matchdays = snapshots
  .map((path) => Number(path.match(/matchday_(\d+)/)?.[1]))
  .filter(Boolean)

const showMatchday = (matchday) => {
  const current = snapshotBatches.value.get(matchday) ?? []
  const previous = snapshotBatches.value.get(matchday - 1) ?? []
  const previousPointsByPlayer = new Map(
    previous.map((player) => [player.playerId, Number(player.totalPoints ?? 0)]),
  )
  const byId = new Map()
  const pointsByPlayer = new Map()

  current.forEach((player) => {
    pointsByPlayer.set(
      player.playerId,
      Number(player.totalPoints ?? 0) - (previousPointsByPlayer.get(player.playerId) ?? 0),
    )
    byId.set(player.playerId, player)
  })

  selectedMatchday.value = matchday
  weeklyPointsByPlayer.value = pointsByPlayer
  players.value = [...byId.values()]
}

const loadSnapshots = async () => {
  try {
    const responses = await Promise.all(snapshots.map((path) => fetch(path)))
    if (responses.some((response) => !response.ok)) {
      throw new Error('Snapshot data could not be loaded.')
    }

    const batches = await Promise.all(responses.map((response) => response.json()))
    snapshotBatches.value = new Map(matchdays.map((matchday, index) => [matchday, batches[index]]))
    showMatchday(Math.max(...matchdays))
  } catch (loadError) {
    error.value = loadError.message
  } finally {
    loading.value = false
  }
}

const normalisedPlayers = computed(() => players.value.map((player) => ({
  id: player.playerId,
  name: player.mediaFirstName && player.mediaLastName
    ? `${player.mediaFirstName} ${player.mediaLastName}`
    : player.mediaShortName,
  team: player.teamShortName,
  teamId: player.teamId,
  position: player.skillName,
  ownership: Number(player.selectedPercentage ?? 0),
  points: Number(player.totalPoints ?? 0),
  averagePoints: Number(player.averagePoints ?? 0),
  thisWeekPoints: weeklyPointsByPlayer.value.get(player.playerId) ?? 0,
  transfersIn: Number(player.transferIn ?? 0),
  transfersOut: Number(player.transferOut ?? 0),
  weekPoints: weeklyPointsByPlayer.value.get(player.playerId) ?? 0,
  matchdayId: player.matchdayId,
  form: player.form,
  league: player.league ?? leagueNames[player.competitionId] ?? 'Unknown',
  imageUrls: playerImageUrls(player),
  imageUrl: playerImageUrls(player)[0] ?? localAssetUrl('user-solid-full.svg'),
  logoUrl: teamLogoUrl(player),
})))

const matchweek = computed(() => selectedMatchday.value)

const latestMatchday = computed(() => Math.max(...matchdays))
const previousMatchday = () => {
  const previous = matchdays.filter((matchday) => matchday < selectedMatchday.value).pop()
  if (previous) showMatchday(previous)
}
const nextMatchday = () => {
  const next = matchdays.find((matchday) => matchday > selectedMatchday.value)
  if (next) showMatchday(next)
}

const weeklyAverage = computed(() => {
  if (!normalisedPlayers.value.length) return 0
  return normalisedPlayers.value.reduce((sum, player) => sum + player.weekPoints, 0) / normalisedPlayers.value.length
})

const bigMisses = computed(() => normalisedPlayers.value
  .filter((player) => player.ownership < 5 && player.weekPoints > 10)
  .sort((a, b) => a.ownership - b.ownership || b.weekPoints - a.weekPoints))

const bigMissCount = computed(() => normalisedPlayers.value
  .filter((player) => player.ownership < 5 && player.weekPoints > 10).length)

const biggestUpsets = computed(() => normalisedPlayers.value
  .filter((player) => player.weekPoints < weeklyAverage.value)
  .sort((a, b) => b.ownership - a.ownership || b.weekPoints - a.weekPoints)
  .slice(0, 10))

const leaderboardCategories = [
  { key: 'points', label: 'Most total points' },
  { key: 'weekPoints', label: 'Most points this week' },
  { key: 'averagePoints', label: 'Most average points' },
  { key: 'ownership', label: 'Most selected' },
  { key: 'transfersIn', label: 'Most transfers in' },
  { key: 'transfersOut', label: 'Most transfers out' },
]

const leaderboardRows = computed(() => leaderboardCategories.map((category) => ({
  ...category,
  players: ['WSL', 'WSL 2'].map((league) => ({
    league,
    player: normalisedPlayers.value
      .filter((candidate) => candidate.league === league)
      .sort((a, b) => b[category.key] - a[category.key])[0],
  })),
})))

const goat = computed(() => normalisedPlayers.value.find(
  (player) => player.id === 'wpll::Football_Player::3ade13d67e974a919693df7eee9bc18f',
))

const visibleSections = computed(() => {
  if (activeView.value === 'misses') return [{ key: 'misses', title: 'Who we missed out on', description: `${bigMissCount.value} players this week scored over 10 points while being selected by less than 5% of managers`, players: bigMisses.value }]
  if (activeView.value === 'upsets') return [{ key: 'upsets', title: 'Who missed out', description: `Top 10 players ranked by selection % who scored less than this week's average points: ${formatPoints(weeklyAverage.value)}`, players: biggestUpsets.value }]
  return [
    { key: 'misses', title: 'Who we missed out on', description: `${bigMissCount.value} players this week scored over 10 points while being selected by less than 5% of managers`, players: bigMisses.value },
    { key: 'upsets', title: 'Who missed out', description: `Top 10 players ranked by selection % who scored less than this week's average points: ${formatPoints(weeklyAverage.value)}`, players: biggestUpsets.value },
    { key: 'leaders', leaderboard: leaderboardRows.value },
  ]
})

const formatPoints = (points) => Number.isInteger(points) ? points : points.toFixed(1)

const leaderboardUnit = (key) => ({
  points: ' Points',
  ownership: '%',
  weekPoints: ' Points',
  averagePoints: ' Points',
  transfersIn: ' Transfers',
  transfersOut: ' Transfers',
}[key] ?? '')

onMounted(loadSnapshots)
</script>

<template>
  <main class="app-shell">
    <header class="masthead">
      <div class="masthead-copy">
        <h1>WSL <br> <span class="fantasy-script">Fantasy Football</span> <br> Weekly Stats</h1>
      </div>
    </header>
      <div class="week-selector" aria-label="Select matchday">
        <button
          v-if="selectedMatchday > Math.min(...matchdays)"
          class="week-arrow week-arrow-previous"
          type="button"
          aria-label="View previous week"
          @click="previousMatchday"
        >&larr;</button>
        <button class="week-button" type="button" @click="showMatchday(selectedMatchday)">
          WEEK {{ matchweek }}
        </button>
        <button
          v-if="selectedMatchday < latestMatchday"
          class="week-arrow week-arrow-next"
          type="button"
          aria-label="View next week"
          @click="nextMatchday"
        >&rarr;</button>
      </div>

    <p v-if="loading" class="state-message">Loading the latest player board...</p>
    <p v-else-if="error" class="state-message error-message">{{ error }}</p>
    <div v-else class="sections">
      <section v-for="section in visibleSections.filter((item) => item.players)" :key="section.key" class="player-section">
        <div class="section-banner-row" :class="`section-banner-row-${section.key}`">
          <div class="section-heading" :class="`section-heading-${section.key}`">
              <div class="section-title-row">
                <h2>{{ section.title }}</h2>
                <div class="section-legend">
                  <span class="status-pill wsl">Pink: WSL</span>
                  <span class="status-pill wsl2">Orange: WSL2</span>
                </div>
              </div>
              <p>{{ section.description }}</p>
          </div>
        </div>

        <div v-if="!section.players.length" class="empty-state">No players this week.</div>
        <div
          v-else
          class="player-rail"
        >
          <article
            v-for="(player, index) in section.players"
            :key="player.id"
            class="player-card"
            :class="[section.key, player.league === 'WSL 2' ? 'league-wsl2' : 'league-wsl']"
            :style="{ '--team-color': clubColorCode[player.teamId] || 'var(--card-accent)' }"
          >
            <div class="card-topline">
              <span class="rank">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="position">{{ player.position }}</span>
            </div>
            <div class="player-image">
              <img :class="{ 'is-fallback': player.imageUrl === '/user-solid-full.svg' }" :src="player.imageUrl" :alt="`${player.name} portrait`" loading="lazy" @error="handlePlayerImageError($event, player)" />
              <img v-if="player.logoUrl" class="team-logo" :src="player.logoUrl" :alt="`${player.team} crest`" loading="lazy" />
            </div>
            <h3>{{ player.name }}</h3>
            <p class="team">
              <span>{{ player.team }}</span>
            </p>
            <div class="card-stats">
              <div>
                  <span>This week</span>
                  <strong>{{ formatPoints(player.weekPoints) }}</strong>
              </div>
              <div>
                <span>Selected</span>
                <strong>{{ player.ownership }}%</strong>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="activeView === 'all'" class="leaderboard-section">
        <div class="leaderboard-track">
          <div class="leaderboard-grid">
          <div v-for="category in leaderboardRows" :key="category.key" class="leaderboard-column">
            <h2>{{ category.label }}</h2>
            <div class="leaderboard-cards">
              <div v-for="row in category.players" :key="row.league" class="leaderboard-row">
                <h3 class="league-row-heading">{{ row.league }}</h3>
                <article
                  v-if="row.player"
                  class="player-card leaderboard-card"
                  :class="row.league === 'WSL 2' ? 'league-wsl2' : 'league-wsl'"
                  :style="{ '--team-color': clubColorCode[row.player.teamId] || 'var(--card-accent)' }"
                >
                  <div class="card-topline">
                    <span class="position">{{ row.player.position }}</span>
                  </div>
                  <div class="player-image">
                    <img :class="{ 'is-fallback': row.player.imageUrl === '/user-solid-full.svg' }" :src="row.player.imageUrl" :alt="`${row.player.name} portrait`" loading="lazy" @error="handlePlayerImageError($event, row.player)" />
                    <img v-if="row.player.logoUrl" class="team-logo" :src="row.player.logoUrl" :alt="`${row.player.team} crest`" loading="lazy" />
                  </div>
                  <h3>{{ row.player.name }}</h3>
                  <p class="team"><span>{{ row.player.team }}</span></p>
                  <div class="card-stats">
                    <div>
                      <strong>{{ formatPoints(row.player[category.key]) }}{{ leaderboardUnit(category.key) }}</strong>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>
            <div v-if="goat" class="leaderboard-column goat-column">
            <h2>GOAT</h2>
            <article
              class="player-card leaderboard-card goat-card league-wsl"
              :style="{ '--team-color': clubColorCode[goat.teamId] || 'var(--card-accent)' }"
            >
              <div class="goat-stars" aria-hidden="true">
                <img class="goat-star goat-star-one" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-two" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-three" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-four" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-five" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-six" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-seven" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-eight" src="/star-solid-full.svg" alt="" />
                <img class="goat-star goat-star-nine" src="/star-solid-full.svg" alt="" />
              </div>
              <div class="card-topline">
                <span class="position">{{ goat.position }}</span>
              </div>
              <div class="player-image">
                <img :class="{ 'is-fallback': goat.imageUrl === '/user-solid-full.svg' }" :src="goat.imageUrl" :alt="`${goat.name} portrait`" loading="lazy" @error="handlePlayerImageError($event, goat)" />
                <img v-if="goat.logoUrl" class="team-logo" :src="goat.logoUrl" :alt="`${goat.team} crest`" loading="lazy" />
              </div>
              <h3>{{ goat.name }}</h3>
              <p class="team"><span>{{ goat.team }}</span></p>
              <div class="card-stats">
                <strong>9999999999999999999999999</strong>
              </div>
            </article>
            </div>
          </div>
        </div>
      </section>
    </div>

  </main>
</template>
