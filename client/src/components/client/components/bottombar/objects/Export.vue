<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Export Objects</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :color="sqlColor" style="margin-right:10px;">SQL</v-btn>
          <v-btn :color="csvColor" style="margin-right:10px;">CSV</v-btn>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <v-tabs v-model="tabObjectsSelected" show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
                    <v-tabs-slider></v-tabs-slider>
                    <v-tab @click="tabObjects('tables')"><span class="pl-2 pr-2">Tables</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                    <v-tab @click="tabObjects('views')"><span class="pl-2 pr-2">Views</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                    <v-tab @click="tabObjects('triggers')"><span class="pl-2 pr-2">Triggers</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                    <v-tab @click="tabObjects('functions')"><span class="pl-2 pr-2">Functions</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                    <v-tab @click="tabObjects('procedures')"><span class="pl-2 pr-2">Procedures</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                    <v-tab @click="tabObjects('events')"><span class="pl-2 pr-2">Events</span></v-tab>
                    <v-divider class="mx-3" inset vertical></v-divider>
                  </v-tabs>
                  <v-data-table v-model="tables" :headers="objectsHeaders.tables" :items="objectsItems.tables" :single-select="false" item-key="name" show-select class="elevation-1"></v-data-table>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="exportObjectsSubmit" color="primary">Export</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Close</v-btn>
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
      loading: false,
      // Dialog
      dialog: false,
      sqlColor: 'primary',
      csvColor: '#779ecb',
      tabObjectsSelected: 0,

      tables: [],
      
      // Axios Cancel Token
      cancelToken: null,
    }
  },
  computed: {
    ...mapFields([
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_EXPORT', this.showDialog);
  },
  methods: {
    showDialog() {
      this.buildObjects()
      this.dialog = true
    },
    tabObjects(object) {
      this.tabObjectsSelected = object
    },
    buildObjects() {
      console.log(this.objectsHeaders)
      console.log(this.objectsItems)
/*
      {
        text: 'Dessert (100g serving)',
        value: 'name',
      },
      */
    },
    exportObjectsSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      axios.get('/client/export', { responseType: 'arraybuffer' })
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'file.sql')
        document.body.appendChild(link)
        link.click()
        link.remove()
      });      
    }
  },
}
</script>