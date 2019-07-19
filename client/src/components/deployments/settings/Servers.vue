<template>
  <div>
    <v-toolbar dark color="primary">
      <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-toolbar-items class="hidden-sm-and-down">
        <v-btn flat @click="newItem()"><v-icon style="padding-right:10px">fas fa-plus-circle</v-icon>NEW</v-btn>
        <v-btn v-if="selected.length == 1" flat @click="editItem()"><v-icon style="padding-right:10px">fas fa-dot-circle</v-icon>EDIT</v-btn>
        <v-btn v-if="selected.length > 0" flat @click="deleteItem()"><v-icon style="padding-right:10px">fas fa-minus-circle</v-icon>DELETE</v-btn>
      </v-toolbar-items>
    </v-toolbar>

    <v-card>
      <v-card-title style="padding-top:0px;">
        <v-text-field v-model="search" append-icon="search" label="Search" single-line hide-details></v-text-field>
      </v-card-title>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" item-key="name" select-all class="elevation-1">
        <template v-slot:items="props">
          <td style="width:5%"><v-checkbox v-model="props.selected" primary hide-details></v-checkbox></td>
          <td>{{ props.item.name }}</td>
          <td>{{ props.item.environment }}</td>
          <td>{{ props.item.region }}</td>
          <td>{{ props.item.hostname }}</td>
          <td>{{ props.item.username }}</td>
          <td>{{ props.item.password }}</td>
        </template>
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="itemDialog" persistent max-width="768px">
      <v-toolbar dark color="primary">
        <v-toolbar-title class="white--text">{{ itemDialogTitle }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <!-- METADATA -->
                <div class="title font-weight-regular" style="padding-top:10px;">Metadata</div>
                <v-text-field ref="field" v-model="item.name" label="Name" required></v-text-field>
                <v-select v-model="item.environment" :items="environments_items" label="Environment" required style="margin-top:0px; padding-top:0px;"></v-select>
                <v-select v-model="item.region" :items="regions_items" label="Region" required style="margin-top:0px; padding-top:0px;"></v-select>
                <!-- SQL -->
                <div class="title font-weight-regular" style="padding-top:10px;">SQL</div>
                <v-text-field v-model="item.hostname" label="Hostname"></v-text-field>
                <v-text-field v-model="item.username" label="Username" style="padding-top:0px;"></v-text-field>
                <v-text-field v-model="item.password" label="Password" style="padding-top:0px;"></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subheading">Are you sure you want to delete the selected servers?</div>
              </v-flex>
              <v-btn color="success" @click="actionConfirm()" dark style="margin-left:0px">Confirm</v-btn>
              <v-btn color="error" @click="itemDialog=false" dark style="margin-left:0px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment'},
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    items: [
      {
        name: 'awseu-rd01',
        environment: 'PROD',
        region: 'AWS-EU',
        hostname: 'awseu-rd01.inbenta.com',
        username: 'dba',
        password: '12345'
      }
    ],
    selected: [],
    search: '',
    // Item
    item: { name: '', environment: '', region: '', hostname: '', username: '', password: '' },
    environments_items: [],
    regions_items: [],
    // Action Mode (new, edit, delete)
    mode: '',
    // Dialog: Item
    itemDialog: false,
    itemDialogTitle: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  methods: {
    getItems() {
      const path = 'http://34.242.255.177:5000/servers'
      axios.get(path)
        .then((res) => {
          this.items = res.data.items
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newItem() {
      this.mode = 'new'
      this.item = { name: '', environment: '', region: '', hostname: '', username: '', password: '' }
      this.itemDialogTitle = 'New Server'
      this.itemDialog = true
    },
    editItem() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.itemDialogTitle = 'Edit Server'
      this.itemDialog = true
    },
    deleteItem() {
      this.mode = 'delete'
      this.itemDialogTitle = 'Delete Server'
      this.itemDialog = true
    },
    actionConfirm() {
      if (this.mode == 'new') this.newItemConfirm()
      else if (this.mode == 'edit') this.editItemConfirm()
      else if (this.mode == 'delete') this.deleteItemConfirm()
    },
    newItemConfirm() {
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.item.name) {
          this.notification('Server currently exists', 'error')
          return
        }
      }
      // Add item in the data table
      this.items.push(this.item)
      this.itemDialog = false
      this.notification('Server added successfully', 'success')
    },
    editItemConfirm() {
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('Server currently exists', 'error')
          return
        }
      }
      // Edit item in the data table
      this.items.splice(i, 1, this.item)
      this.itemDialog = false
      this.notification('Server edited successfully', 'success')
    },
    deleteItemConfirm() {
      while(this.selected.length > 0) {
        var s = this.selected.pop()
        for (var i = 0; i < this.items.length; ++i) {
          if (this.items[i]['name'] == s['name']) {
            // Delete Item
            this.items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected servers removed successfully', 'success')
      this.itemDialog = false
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    itemDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script> 