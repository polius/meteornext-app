<template>
  <div>
    <!---------------->
    <!-- NEW FOLDER -->
    <!---------------->
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:2px">fas fa-folder-plus</v-icon>NEW FOLDER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" @submit.prevent style="margin-top:15px; margin-bottom:15px">
                  <v-text-field @keyup.enter="newFolderSubmit" v-model="name" :rules="[v => !!v || '']" label="Folder Name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="newFolderSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      name: '',
    }
  },
  computed: {
    ...mapFields([
      'servers',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-servers-new-folder', this.newFolder)
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (val) this.name = ''
      else {
        requestAnimationFrame(() => {
          if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        })
      }
    }
  },
  methods: {
    newFolder() {
      this.dialog = true
    },
    newFolderSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      this.loading = true
      const payload = { 'folder': this.name }
      axios.post('/client/servers', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 2)
          this.dialog = false
          // Get servers + select new folder
          new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
          .then(() => {
            const folder = this.servers.find(x => 'children' in x && x.name == this.name)
            this.sidebarSelected = [folder]
          })
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
  }
}
</script>