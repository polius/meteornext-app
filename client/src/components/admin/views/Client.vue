<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>CLIENT</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-tabs background-color="primary" color="white" v-model="tabs" slider-color="white" slot="extension">
            <v-tab title="Show Executed Queries"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>QUERIES</span></v-tab>
            <v-tab title="Show Attached / Detached Servers"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-server</v-icon>SERVERS</span></v-tab>
          </v-tabs>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="filterClick" text class="body-2" :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refreshClick" text class="body-2"><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field append-icon="search" label="Search" @input="onSearch" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <Queries v-show="tabs == 0" />
      <Servers v-show="tabs == 1" />
    </v-card>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import Queries from './client/Queries'
import Servers from './client/Servers'

export default {
  data() {
    return {
      tabs: 0,
      filterApplied: false,
    }
  },
  components: { Queries, Servers },
  mounted() {
    EventBus.$on('client-toggle-filter', (value) => { this.filterApplied = value })
  },
  methods: {
    onSearch(value) {
      if (this.tabs == 0) EventBus.$emit('search-client-queries', value)
      else EventBus.$emit('search-client-servers', value)
    },
    filterClick() {
      if (this.tabs == 0) EventBus.$emit('filter-client-queries')
      else EventBus.$emit('filter-client-servers')
    },
    refreshClick() {
      if (this.tabs == 0) EventBus.$emit('refresh-client-queries')
      else EventBus.$emit('refresh-client-servers')
    },
  },
}
</script>