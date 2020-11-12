<template>
  <div>
    <!-------------------->
    <!-- NEW CONNECTION -->
    <!-------------------->
    <v-dialog v-model="dialog" persistent max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">New Connection</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="selected.length == 0 || loading" :loading="loading" @click="newConnectionSubmit" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:10px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:5px; margin-bottom:10px;">
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="search" @input="onServerSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding:0px;">
                      <Splitpanes @ready="onSplitPaneReady" style="height:71vh">
                        <Pane size="30" min-size="0" style="align-items:inherit">
                          <v-container fluid style="padding:0px;">
                            <v-row no-gutters style="height:calc(100% - 36px); overflow:auto;">
                              <v-list flat style="width:100%; padding:0px;">
                                <v-list-item-group mandatory multiple>
                                  <v-list-item v-for="item in items" :key="item.id" dense @click="onServerClick(item)" @contextmenu="$event.preventDefault()" style="max-height:20px;">
                                    <template>
                                      <v-list-item-action style="margin-right:15px">
                                        <v-checkbox dense :input-value="selected.includes(item.id)"></v-checkbox>
                                      </v-list-item-action>
                                      <v-list-item-content>
                                        <v-list-item-title><v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? 'error' : 'warning'" style="margin-right:10px; margin-bottom:2px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.name }}</v-list-item-title>
                                      </v-list-item-content>
                                    </template>
                                  </v-list-item>
                                </v-list-item-group>
                              </v-list>
                            </v-row>
                            <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
                              <v-btn @click="refresh" :loading="loading" :disabled="loading" text small title="Refresh Servers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="selectAll" text small title="Select All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-check-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                              <v-btn @click="deselectAll" text small title="Deselect All" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">far fa-square</v-icon></v-btn>
                              <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
                            </v-row>
                          </v-container>
                        </Pane>
                        <Pane size="70" min-size="0" style="align-items:inherit; background-color:#484848; padding:0px 2% 2% 2%; overflow-y:auto;">
                          <v-container style="max-width:100%;">
                            <v-layout wrap>
                              <v-flex v-if="Object.keys(item).length == 0" xs12>
                                <div class="body-2" style="text-align:center; margin-top:2%;">Select a server to show the details</div>
                              </v-flex>
                              <v-flex v-else>
                                <v-row justify="space-around">
                                  <v-img :src="require('@/assets/amazon_aurora.png')" class="my-3" contain height="100"></v-img>
                                </v-row>
                                <v-row justify="space-around" style="margin-top:10px">
                                  <div class="text-h5">{{ item.name }}</div>
                                </v-row>
                                <v-row justify="space-around" style="margin-top:10px">
                                  <div class="text-subtitle-1"><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-users</v-icon>{{ item.region }}</div>
                                </v-row>
                                <v-row no-gutters style="margin-top:25px">
                                  <v-col cols="8" style="padding-right:10px">
                                    <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px;"></v-text-field>
                                  </v-col>
                                  <v-col cols="4" style="padding-left:10px">
                                    <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px;"></v-text-field>
                                  </v-col>
                                </v-row>
                                <v-row no-gutters style="margin-top:5px">
                                  <v-col cols="8" style="padding-right:10px">
                                    <v-text-field v-model="item.hostname" readonly label="Hostname" required style="padding-top:0px;"></v-text-field>
                                  </v-col>
                                  <v-col cols="4" style="padding-left:10px">
                                    <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px;"></v-text-field>
                                  </v-col>
                                </v-row>
                                <v-text-field v-model="item.username" readonly label="Username" hide-details required style="padding-top:0px; margin-top:10px"></v-text-field>
                                <v-text-field v-model="item.password" readonly label="Password" hide-details style="margin-top:20px"></v-text-field>
                                <v-switch v-model="item.ssl" readonly flat label="Use SSL" style="margin-top:25px"></v-switch>
                              </v-flex>
                            </v-layout>
                          </v-container>
                        </Pane>
                      </Splitpanes>
                    </v-card-text>
                  </v-card>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/splitPanes.css"></style>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      search: '',
      servers: [],
      items: [],
      selected: [],
      item: {},
    }
  },
  components: { Splitpanes, Pane },
  computed: {
    ...mapFields([
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  created() {
    this.getServers()
  },
  mounted() {
    EventBus.$on('show-bottombar-connections-new', this.newConnection)
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
    },
  },
  methods: {
    onSplitPaneReady() {

    },
    getServers() {
      this.loading = true
      axios.get('/inventory/servers')
        .then((response) => {
          this.servers = response.data.data
          this.items = response.data.data
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => this.loading = false )
    },
    onServerSearch(value) {
      if (value.length == 0) this.items = this.servers.slice(0)
      else this.items = this.servers.filter(x => x.name.toLowerCase().includes(value.toLowerCase()))
    },
    onServerClick(item) {
      const index = this.selected.findIndex(x => x == item.id)
      if (index > -1) this.selected.splice(index, 1)
      else this.selected.push(item.id)
      // Select the server to display
      if (this.selected.length == 0) this.item = {}
      else if (this.selected[this.selected.length - 1].id == item.id) this.item = JSON.parse(JSON.stringify(item))
      else this.item = this.servers.find(x => x.id == this.selected[this.selected.length - 1])
    },
    newConnection() {
      this.dialog = true
    },
    newConnectionSubmit() {
      this.dialog = false
    },
    refresh() {
      this.getServers()
    },
    selectAll() {
      this.selected = this.servers.map(x => x.id)
      if (Object.keys(this.item).length == 0) this.item = JSON.parse(JSON.stringify(this.servers[this.servers.length - 1]))
    },
    deselectAll() {
      this.selected = []
      this.item = {}
    },
  }
}
</script>