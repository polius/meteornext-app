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
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <Queries v-show="tabs == 0" :search="search" />
      <Servers v-show="tabs == 1" :search="search" />
    </v-card>
    <v-dialog v-model="serverDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">SERVER</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn readonly title="Create the server only for a user" :color="!server.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn readonly title="Create the server for all users in a group" :color="server.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="serverDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px;">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete readonly v-model="server.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!server.shared" style="margin-left:20px">
                      <v-autocomplete readonly v-model="server.owner_id" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly ref="name" v-model="server.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-autocomplete readonly v-model="server.region_id" item-value="id" item-text="name" :rules="[v => !!v || '']" :items="[server.region_id]" label="Region" required>
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ server.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ server.name }}
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-select readonly v-model="server.engine" :items="[server.engine]" label="Engine" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select readonly v-model="server.version" :items="[server.version]" label="Version" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <div style="margin-bottom:20px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field readonly v-model="server.hostname" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field readonly v-model="server.port" :rules="[v => v == parseInt(v) || '']" label="Port" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field readonly v-model="server.username" :rules="[v => !!v || '']" label="Username" required style="padding-top:0px;"></v-text-field>
                    <v-text-field readonly v-model="server.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" hide-details></v-text-field>
                    <v-select readonly outlined v-model="server.usage" :items="[server.usage]" :menu-props="{ top: true, offsetY: true }" label="Usage" multiple hide-details item-color="rgb(66,66,66)" style="margin-top:20px"></v-select>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="info" @click="serverDialog = false">CLOSE</v-btn>
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
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
      search: '',
      filterApplied: false,
      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,
    }
  },
  components: { Queries, Servers },
  mounted() {
    EventBus.$on('client-toggle-filter', (value) => { this.filterApplied = value })
  },
  methods: {
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