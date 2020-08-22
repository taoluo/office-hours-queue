import React, { useState } from "react";
import { Modal } from "semantic-ui-react";
import NewUserForm from "../Forms/NewUserForm";
import VerificationForm from "../../AccountSettings/VerificationForm";

const NewUserModal = ({ open, user, closeFunc, refetch, setToast, mutate }) => {
    const [modalView, setModalView] = useState("info");

    return (
        <Modal open={open}>
            <Modal.Content>
                {modalView === "info" ? (
                    <NewUserForm
                        user={user}
                        setModalView={setModalView}
                        closeFunc={closeFunc}
                        refetch={refetch}
                        setToast={setToast}
                    />
                ) : (
                    <VerificationForm
                        // setModalView={setModalView}
                        toastFunc={setToast}
                        openFunc={closeFunc}
                        mutate={mutate}
                    />
                )}
            </Modal.Content>
        </Modal>
    );
};

export default NewUserModal;