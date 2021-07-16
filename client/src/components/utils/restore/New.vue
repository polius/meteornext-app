<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW RESTORE</v-toolbar-title>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/utils/restore"><v-btn icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn></router-link>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-form ref="form" style="padding:5px">
              <div class="text-subtitle-1 font-weight-regular white--text">SOURCE</div>
              <v-radio-group v-model="source" style="margin-top:10px; margin-bottom:20px" hide-details>
                <v-radio value="file">
                  <template v-slot:label>
                    <div>File</div>
                  </template>
                </v-radio>
                <v-radio value="url">
                  <template v-slot:label>
                    <div>URL</div>
                  </template>
                </v-radio>
                <v-radio value="s3">
                  <template v-slot:label>
                    <div>Amazon S3</div>
                  </template>
                </v-radio>
              </v-radio-group>
              <v-file-input outlined v-show="source == 'file'" v-model="file" show-size accept=".sql" label="Click to import a .sql file" prepend-icon truncate-length="100" hide-details></v-file-input>
              <v-text-field outlined v-show="source == 'url'" v-model="url" label="URL" :rules="[v => !!v || '']" hide-details></v-text-field>
              <div class="text-subtitle-1 font-weight-regular white--text" style="margin-top:20px">DESTINATION</div>
              <v-autocomplete v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" :rules="[v => !!v || '']" style="margin-top:10px">
                <template v-slot:[`selection`]="{ item }">
                  <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                  {{ item.name }}
                </template>
                <template v-slot:[`item`]="{ item }">
                  <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                  {{ item.name }}
                </template>
              </v-autocomplete>
              <v-text-field v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:0px" hide-details></v-text-field>
              <v-divider style="margin-top:20px"></v-divider>
              <div style="margin-top:20px">
                <v-btn :loading="loading" color="#00b16a" @click="submitRestore()">RESTORE</v-btn>
                <router-link to="/utils/restore"><v-btn :disabled="loading" color="#EF5354" style="margin-left:5px">CANCEL</v-btn></router-link>
              </div>
            </v-form>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
  </div>
</template>

<style scoped>
::v-deep .v-toolbar__content {
  padding-right:5px;
}
</style>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      loading: false,
      serverItems: [],
      server: '',
      database: '',
      source: 'file',
      file: null,
      url: '',
    }
  },
  created() {
    this.getServers()
  },
  methods: {
    getServers() {
      this.loading = true
      axios.get('/restore/servers')
        .then((response) => {
          this.serverItems = response.data.servers
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    submitRestore() {

    },
  }
}
</script>