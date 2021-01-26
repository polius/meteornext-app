<template>
  <v-main>
    <Header/>
    <v-container fluid>
      <v-main style="padding-top:0px; padding-bottom:0px;">
        <div style="margin: -12px;">
          <div ref="masterDiv" style="height: calc(100vh - 112px);">
            <Connections />
            <Splitpanes :style="(Object.keys(server).length != 0 || connections.length > 1) ? 'height:calc(100% - 49px)' : 'height:100%'">
              <Pane size="21" min-size="0">
                <Sidebar />
              </Pane>
              <Pane size="79" min-size="0">
                <div style="height:100%; width:100%">
                  <Main />
                </div>
              </Pane>
            </Splitpanes>
          </div>
        </div>
      </v-main>
    </v-container>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-main>
</template>

<style scoped src="@/styles/splitPanes.css"></style>
<style scoped>
@import "../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";

/* ACE EDITOR */
::v-deep .ace_editor {
  margin: auto;
  height: 100%;
  width: 100%;
  background: #272822;
}
::v-deep .ace_content {
  width: 100%;
  height: 100%;
}

/* TREEVIEW */
::v-deep .v-treeview-node__root {
  min-height:30px;
  padding-right:0px;
}
::v-deep .v-treeview-node__toggle {
  width: 15px;
}
::v-deep .v-treeview-node__level {
  width: 10px;
}

/* DATA TABLE */
::v-deep .theme--dark.v-data-table.v-data-table--fixed-header thead th {
  background-color: #252525;
}

/* LABEL */
::v-deep .v-label{
  font-size: 0.9rem;
}

/* INPUT */
::v-deep .v-input {
  font-size: 0.9rem;
}

/* APPLICATION */
::v-deep .v-application .elevation-2 {
  box-shadow:none!important;
}

/* CONTAINER */
::v-deep .container {
  padding-bottom:0px;
}
::v-deep .v-text-field .v-input__control .v-input__slot {
  min-height: auto !important;
  display: flex !important;
  align-items: center !important;
}
::v-deep *
{
  will-change: auto !important;
}
::v-deep .ace_editor.ace_autocomplete {
  width: 512px;
}
/* AG GRID */
::v-deep .ag-theme-alpine-dark .ag-header-row {
  font-size: 13px;
  font-weight: 500;
}
::v-deep .ag-theme-alpine-dark .ag-cell {
  font-size: 13px;
  line-height: 30px;
}
::v-deep .ag-theme-alpine-dark .ag-cell-inline-editing {
  height: 30px;
}
::v-deep .ag-theme-alpine-dark {
  --ag-foreground-color:#dcdcdc;
  --ag-header-background-color:#272727;
  --ag-background-color:#2c2c2c;
  --ag-odd-row-background-color:#303030;
  --ag-border-color:#424242;
}
::v-deep .ag-cell-normal {
  color: #dcdcdc;
}
::v-deep .ag-cell-null {
  color: gray;
}
::v-deep tr:hover {
  background-color: transparent !important;
}
</style>

<script>
import axios from 'axios'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import Header from './components/Header'
import Connections from './components/Connections'
import Sidebar from './components/Sidebar'
import Main from './components/Main'

import { mapFields } from './js/map-fields'
import EventBus from './js/event-bus'

export default {
  data() {
    return {
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: '',
    }
  },
  components: { Splitpanes, Pane, Header, Connections, Sidebar, Main },
  computed: {
    ...mapFields([
      'connections',
      'settings',
    ], { path: 'client/client' }),
    ...mapFields(['server'], { path: 'client/connection' }),
  },
  beforeMount() {
    window.addEventListener('beforeunload', this.beforeUnload)
  },
  created() {
    this.getSettings()
  },
  mounted() {
    EventBus.$on('send-notification', this.notification);
  },
  beforeDestroy() {
    EventBus.$off()
    this.$store.dispatch('client/reset')
    window.removeEventListener('beforeunload', this.beforeUnload)
  },
  // eslint-disable-next-line
  beforeRouteLeave(to, from, next) {
    if (to.name == 'login') next()
    else {
      const answer = window.confirm('Close Meteor Next - Client?')
      if (answer) next()
      else next(false)
    }
  },
  methods: {
    getSettings() {
      axios.get('/client/settings')
        .then((response) => {
          // Get stored user values
          let data = response.data.settings
          for (let row of data) this.settings[row.setting] = row.value
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    notification(message, color='', timeout=5) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbarTimeout = Number(timeout*1000)
      this.snackbar = true
    },
    beforeUnload(e) {
      e.preventDefault() 
      e.returnValue = ''
    },
  },
}
</script>