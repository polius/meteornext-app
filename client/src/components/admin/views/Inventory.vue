<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="#3a529b">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-layer-group</v-icon>INVENTORY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn :depressed="filterApplied" :color="filterApplied ? '#4a66a1' : ''" @click="filterClick" text class="body-2"><v-icon small style="padding-right:10px">fas fa-search</v-icon>FILTER</v-btn>
          <v-btn @click="newClick" text class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" @click="editClick" text class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" @click="deleteClick" text class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tabs v-model="tab" background-color="transparent" color="white" slider-color="white" slot="extension">
            <v-tab>ENVIRONMENTS</v-tab>
            <v-tab>REGIONS</v-tab>
            <v-tab>SERVERS</v-tab>
            <v-tab>AUXILIARY</v-tab>
          </v-tabs>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="filter.search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <Environments v-show="tab == 0" :groups="groups" :filter="filter"/>
    </v-card>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:25px;">
                  <v-autocomplete ref="filter" v-model="filter.group" filled :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-bottom:20px"></v-autocomplete>
                  <v-row no-gutters style="margin-bottom:12px;">
                    <v-col cols="auto">
                      <div class='text-subtitle-1 font-weight-regular'>Scope:</div>
                    </v-col>
                    <v-col cols="auto" style="margin-left:10px;">
                      <v-radio-group v-model="filter.scope" row hide-details style="margin-top:0px; padding-top:2px">
                        <v-radio label="All" value="all"></v-radio>
                        <v-radio label="Personal" value="personal" color="warning"></v-radio>
                        <v-radio label="Shared" value="shared" color="error"></v-radio>
                      </v-radio-group>
                    </v-col>
                  </v-row>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="filterInventory()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="dialog = false" style="margin-left:5px;">Cancel</v-btn>
                    <v-btn v-if="filterApplied" :disabled="loading" color="info" @click="clearFilter()" style="float:right;">Remove Filter</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------->
    <!-- SNACKBAR -->
    <!-------------->
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import axios from 'axios'
import Environments from './inventory/Environments'

export default {
  data() {
    return {
      tab: '',
      selected: [],
      // Dialog
      dialog: false,
      loading: false,
      groups: [],
      filter: { search: '', group: null, scope: 'all'},
      filterApplied: false,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  components: { Environments },
  created() {
    this.getGroups()
  },
  mounted() {
    EventBus.$on('notification', this.notification)
    EventBus.$on('change-selected', this.changeSelected)
  },
  methods: {
    getGroups() {
      axios.get('/admin/inventory/groups')
        .then((response) => {
          this.groups = response.data.groups
        })
        .catch((error) => {
          console.log(error)
        })
    },
    newClick() {
      if (this.tab == 0) EventBus.$emit('new-environment')
      else if (this.tab == 1) EventBus.$emit('new-region')
      else if (this.tab == 2) EventBus.$emit('new-server')
      else if (this.tab == 3) EventBus.$emit('new-auxiliary')
    },
    editClick() {
      if (this.tab == 0) EventBus.$emit('edit-environment')
      else if (this.tab == 1) EventBus.$emit('edit-region')
      else if (this.tab == 2) EventBus.$emit('edit-server')
      else if (this.tab == 3) EventBus.$emit('edit-auxiliary')
    },
    deleteClick() {
      if (this.tab == 0) EventBus.$emit('delete-environment')
      else if (this.tab == 1) EventBus.$emit('delete-region')
      else if (this.tab == 2) EventBus.$emit('delete-server')
      else if (this.tab == 3) EventBus.$emit('delete-auxiliary')
    },
    filterClick() {
      this.dialog = true
    },
    filterInventory() {
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      if (this.tab == 0) EventBus.$emit('filter-environments')
      else if (this.tab == 1) EventBus.$emit('filter-regions')
      else if (this.tab == 2) EventBus.$emit('filter-servers')
      else if (this.tab == 3) EventBus.$emit('filter-auxiliary')
      this.filterApplied = true
      this.dialog = false
    },
    clearFilter() {
      this.filter = { search: '', group: null, scope: 'all' }
      this.$nextTick(() => {
        if (this.tab == 0) EventBus.$emit('filter-environments')
        else if (this.tab == 1) EventBus.$emit('filter-regions')
        else if (this.tab == 2) EventBus.$emit('filter-servers')
        else if (this.tab == 3) EventBus.$emit('filter-auxiliary')
      })
      this.filterApplied = false
      this.dialog = false
    },
    changeSelected(val) {
      this.selected = val
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (!this.filterApplied) this.filter = { search: '', group: null, scope: 'all' }
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.filter !== 'undefined') this.$refs.filter.focus()
      })
    },
  },
}
</script>